from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec, SerializedScoreDocument
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.score.draft_store import DraftNotFoundError
from piano_app.domain.score.document import ScoreDocument

from ..schema import DraftORM


class PostgresDraftArchive:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        codec: ScoreDocumentCodec,
    ) -> None:
        self._session_factory: async_sessionmaker[AsyncSession] = session_factory
        self._codec: ScoreDocumentCodec = codec

    async def create(
        self,
        *,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> DraftSnapshot:
        initial_version: int = 0
        orm: DraftORM = DraftORM(
            author_id=author_id,
            score_id=ref_score_id,
            revisions=[self._codec.serialize(document)],
            cursor=0,
            version=initial_version,
        )
        # flush and then commit because the contract does not guarantee
        # expire_on_commit=False on sessionmaker
        async with self._session_factory() as session:
            session.add(orm)
            await session.flush()
            draft_id: str = orm.id
            await session.commit()

        return DraftSnapshot.create(
            draft_id=draft_id,
            author_id=author_id,
            ref_score_id=ref_score_id,
            revisions=[document],
            cursor=0,
            version=initial_version,
        )

    async def archive(self, *, snapshot: DraftSnapshot) -> None:
        revisions: list[SerializedScoreDocument] = [
            self._codec.serialize(revision) for revision in snapshot.revisions
        ]
        async with self._session_factory() as session:
            updated_draft_id: str | None = await session.scalar(
                update(DraftORM)
                .where(
                    DraftORM.id == snapshot.draft_id,
                    DraftORM.version < snapshot.version,
                )
                .values(
                    revisions=revisions,
                    cursor=snapshot.cursor,
                    version=snapshot.version,
                )
                .returning(DraftORM.id)
            )
            # if updated_draft_id is not None, then succesfully updated
            if updated_draft_id is not None:
                await session.commit()
                return

            # if it is None, then the reason it is None is to be determined
            stored_id: str | None = await session.scalar(
                select(DraftORM.id).where(DraftORM.id == snapshot.draft_id)
            )
            # if the id is None, then the draft does not exist
            if stored_id is None:
                raise DraftNotFoundError(draft_id=snapshot.draft_id)

            # otherwise, 'snapshot.version' is outdated and the latter version is already archived
            # so we do nothing
            return

    async def restore(self, *, draft_id: str) -> DraftSnapshot:
        async with self._session_factory() as session:
            orm: DraftORM | None = await session.get(DraftORM, draft_id)
            if orm is None:
                raise DraftNotFoundError(draft_id=draft_id)

            return orm.to_snapshot(codec=self._codec)
