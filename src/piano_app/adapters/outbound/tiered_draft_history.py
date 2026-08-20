import asyncio
from collections.abc import Sequence
from typing import Protocol

from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.score import (
    DraftMeta,
    DraftStoreNotFoundError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument


class DraftArchive(Protocol):
    """Cold-tier draft storage, nothing runs "on" cold (no commit/undo/redo),
     archive/get_snapshot just move a whole `DraftSnapshot` in/out of durable storage.
     list_by_author is the one read that never goes through hot (see `TieredDraftHistory.
     list_by_author`) — cold is the only tier guaranteed to hold every draft, not just
     the currently-hot ones.

    `TieredDraftHistory`'s own dependency contract.
    """

    async def create(
        self,
        *,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> DraftSnapshot: ...

    async def archive(self, *, snapshot: DraftSnapshot) -> None: ...

    async def get_snapshot(self, *, draft_id: str) -> DraftSnapshot | None: ...

    async def list_by_author(self, *, author_id: str) -> Sequence[DraftMeta]: ...


class DraftCache(Protocol):
    """Hot-tier draft storage is the fast store `TieredDraftHistory` reads/writes on
    the request path.

    Defined here, not inherited from the `DraftHistory` application port. This is
    `TieredDraftHistory`'s own contract.
    """

    async def get(self, *, draft_id: str) -> VersionedDraftDocument | None: ...

    async def undo(self, *, draft: VersionedDraftDocument) -> bool: ...

    async def redo(self, *, draft: VersionedDraftDocument) -> bool: ...

    async def commit(self, *, draft: VersionedDraftDocument) -> None: ...

    async def hydrate(self, *, snapshot: DraftSnapshot) -> None: ...

    async def load_snapshot(self, *, draft_id: str) -> DraftSnapshot: ...


class TieredDraftHistory:
    def __init__(self, *, archive: DraftArchive, cache: DraftCache) -> None:
        self._hot: DraftCache = cache
        self._cold: DraftArchive = archive
        self._archive_tasks: set[asyncio.Task[None]] = set()

    async def create(
        self,
        *,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        snapshot: DraftSnapshot = await self._cold.create(
            title=title,
            author_id=author_id,
            ref_score_id=ref_score_id,
            document=document,
        )
        await self._hot.hydrate(snapshot=snapshot)
        return VersionedDraftDocument.create(
            draft_id=snapshot.draft_id,
            title=snapshot.title,
            author_id=snapshot.author_id,
            ref_score_id=snapshot.ref_score_id,
            updated_at=snapshot.updated_at,
            document=snapshot.revisions[snapshot.cursor],
            version=snapshot.version,
        )

    # cold only, no need for a fast cache for this operation
    async def list_by_author(self, *, author_id: str) -> Sequence[DraftMeta]:
        return await self._cold.list_by_author(author_id=author_id)

    async def get(self, *, draft_id: str) -> VersionedDraftDocument | None:
        """Gets a draft from the hot tier, restoring from cold if necessary."""
        draft: VersionedDraftDocument | None = await self._hot.get(draft_id=draft_id)
        if draft is not None:
            return draft

        if not await self._restore(draft_id=draft_id):
            return None

        return await self._hot.get(draft_id=draft_id)

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        undone: bool
        try:
            undone = await self._hot.undo(draft=draft)
        except DraftStoreNotFoundError:
            if not await self._restore(draft_id=draft.draft_id):
                raise DraftStoreNotFoundError(draft_id=draft.draft_id) from None

            undone = await self._hot.undo(draft=draft)

        if undone:
            self._schedule_archive(draft_id=draft.draft_id)

        return undone

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        redone: bool
        try:
            redone = await self._hot.redo(draft=draft)
        except DraftStoreNotFoundError:
            if not await self._restore(draft_id=draft.draft_id):
                raise DraftStoreNotFoundError(draft_id=draft.draft_id) from None

            redone = await self._hot.redo(draft=draft)

        if redone:
            self._schedule_archive(draft_id=draft.draft_id)

        return redone

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        try:
            await self._hot.commit(draft=draft)
        except DraftStoreNotFoundError:
            if not await self._restore(draft_id=draft.draft_id):
                raise DraftStoreNotFoundError(draft_id=draft.draft_id) from None

            await self._hot.commit(draft=draft)

        self._schedule_archive(draft_id=draft.draft_id)

    async def aclose(self) -> None:
        if self._archive_tasks:
            await asyncio.gather(*self._archive_tasks, return_exceptions=True)

    async def _restore(self, *, draft_id: str) -> bool:
        snapshot: DraftSnapshot | None = await self._cold.get_snapshot(draft_id=draft_id)
        if snapshot is None:
            return False

        await self._hot.hydrate(snapshot=snapshot)
        return True

    async def _archive(self, *, draft_id: str) -> None:
        try:
            snapshot: DraftSnapshot = await self._hot.load_snapshot(draft_id=draft_id)
            await self._cold.archive(snapshot=snapshot)
        except Exception:
            # TODO log here
            return

    def _schedule_archive(self, *, draft_id: str) -> None:
        task: asyncio.Task[None] = asyncio.create_task(self._archive(draft_id=draft_id))
        self._archive_tasks.add(task)
        task.add_done_callback(self._archive_tasks.discard)
