from collections.abc import Sequence

from sqlalchemy import Result, Row, ScalarResult, Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from piano_app.adapters.outbound.postgres.draft.schema import DraftContentModel, DraftMetaModel
from piano_app.adapters.outbound.shared.codec import (
    ScoreDocumentCodec,
    SerializedScoreDocument,
)
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.score import DraftMeta, DraftStoreNotFoundError
from piano_app.domain.score.document import ScoreDocument


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
        title: str,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> DraftSnapshot:
        async with self._session_factory() as session:
            meta: DraftMetaModel = DraftMetaModel(
                title=title,
                author_id=author_id,
                score_id=ref_score_id,
            )
            session.add(meta)
            await session.flush()

            content: DraftContentModel = DraftContentModel(
                id=meta.id,
                revisions=[self._codec.serialize(document)],
                cursor=0,
                version=0,
            )
            session.add(content)

            # built before commit: commit() may expire meta/content's attributes,
            snapshot: DraftSnapshot = self._to_snapshot(meta=meta, content=content)
            await session.commit()

        return snapshot

    async def archive(self, *, snapshot: DraftSnapshot) -> None:
        async with self._session_factory() as session:
            revisions: list[SerializedScoreDocument] = [
                self._codec.serialize(revision) for revision in snapshot.revisions
            ]
            updated_content_id: str | None = await session.scalar(
                update(DraftContentModel)
                .where(
                    DraftContentModel.id == snapshot.draft_id,
                    DraftContentModel.version < snapshot.version,
                )
                .values(
                    revisions=revisions,
                    cursor=snapshot.cursor,
                    version=snapshot.version,
                )
                .returning(DraftContentModel.id)
            )
            if updated_content_id is not None:
                await session.execute(
                    update(DraftMetaModel)
                    .where(DraftMetaModel.id == snapshot.draft_id)
                    .values(updated_at=func.now())
                )
                await session.commit()
                return

            # check if the draft is non-existent or simply a version has already moved forward
            stored_id: str | None = await session.scalar(
                select(DraftMetaModel.id).where(DraftMetaModel.id == snapshot.draft_id)
            )
            if stored_id is None:
                raise DraftStoreNotFoundError(draft_id=snapshot.draft_id)

    async def get_snapshot(self, *, draft_id: str) -> DraftSnapshot | None:
        async with self._session_factory() as session:
            statement: Select[tuple[DraftMetaModel, DraftContentModel]] = (
                select(DraftMetaModel, DraftContentModel)
                .join(DraftContentModel, DraftContentModel.id == DraftMetaModel.id)
                .where(DraftMetaModel.id == draft_id)
            )
            result: Result[tuple[DraftMetaModel, DraftContentModel]] = await session.execute(
                statement
            )
            result_row: Row[tuple[DraftMetaModel, DraftContentModel]] | None = result.one_or_none()

            if result_row is None:
                return None

            return self._to_snapshot(
                meta=result_row[0],
                content=result_row[1],
            )

    async def list_by_author(self, *, author_id: str) -> Sequence[DraftMeta]:
        async with self._session_factory() as session:
            statement: Select[tuple[DraftMetaModel]] = select(DraftMetaModel).where(
                DraftMetaModel.author_id == author_id
            )
            result: ScalarResult[DraftMetaModel] = await session.scalars(statement)
            return [row.to_meta() for row in result.all()]

    def _to_snapshot(
        self,
        *,
        meta: DraftMetaModel,
        content: DraftContentModel,
    ) -> DraftSnapshot:
        return DraftSnapshot.create(
            draft_id=meta.id,
            title=meta.title,
            author_id=meta.author_id,
            ref_score_id=meta.score_id,
            updated_at=meta.updated_at,
            revisions=[self._codec.deserialize(revision) for revision in content.revisions],
            cursor=content.cursor,
            version=content.version,
        )
