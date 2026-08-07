import asyncio
from typing import Protocol

from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.draft_store import (
    DraftNotFoundError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument


# TODO add an implementation with archive that uses UOW inside if more that 1 table for drafts
class DraftArchive(Protocol):
    """Cold-tier draft storage, nothing runs "on" cold (no commit/undo/redo),
     archive/restore just move a whole `DraftSnapshot` in/out of durable storage.

    `TieredDraftHistory`'s own dependency contract.
    """

    async def create(
        self,
        *,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> DraftSnapshot: ...
    async def archive(self, *, snapshot: DraftSnapshot) -> None: ...
    async def restore(self, *, draft_id: str) -> DraftSnapshot: ...


class DraftCache(Protocol):
    """Hot-tier draft storage is the fast store `TieredDraftHistory` reads/writes on
    the request path.

    Defined here, not inherited from the `DraftHistory` application port. This is
    `TieredDraftHistory`'s own contract.
    """

    async def load(self, *, draft_id: str) -> VersionedDraftDocument: ...

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
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        snapshot: DraftSnapshot = await self._cold.create(
            author_id=author_id,
            ref_score_id=ref_score_id,
            document=document,
        )
        await self._hot.hydrate(snapshot=snapshot)
        return VersionedDraftDocument(
            draft_id=snapshot.draft_id,
            document=snapshot.revisions[snapshot.cursor],
            version=snapshot.version,
            author_id=snapshot.author_id,
            ref_score_id=snapshot.ref_score_id,
        )

    async def load(self, *, draft_id: str) -> VersionedDraftDocument:
        """Tries to load a draft from the hot tier, restoring from cold if necessary."""
        try:
            return await self._hot.load(draft_id=draft_id)
        except DraftNotFoundError:
            await self._restore(draft_id=draft_id)

            return await self._hot.load(draft_id=draft_id)

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        undone: bool
        try:
            undone = await self._hot.undo(draft=draft)
        except DraftNotFoundError:
            await self._restore(draft_id=draft.draft_id)
            undone = await self._hot.undo(draft=draft)

        if undone:
            self._schedule_archive(draft_id=draft.draft_id)

        return undone

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        redone: bool
        try:
            redone = await self._hot.redo(draft=draft)
        except DraftNotFoundError:
            await self._restore(draft_id=draft.draft_id)
            redone = await self._hot.redo(draft=draft)

        if redone:
            self._schedule_archive(draft_id=draft.draft_id)

        return redone

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        try:
            await self._hot.commit(draft=draft)
        except DraftNotFoundError:
            await self._restore(draft_id=draft.draft_id)
            await self._hot.commit(draft=draft)

        self._schedule_archive(draft_id=draft.draft_id)

    async def aclose(self) -> None:
        if self._archive_tasks:
            await asyncio.gather(*self._archive_tasks, return_exceptions=True)

        # the hot tier isn't part of the DraftCache contract (not every cache
        # needs closing — e.g. a future in-process one wouldn't), so this is a
        # duck-typed best-effort close, not a protocol method.
        hot_aclose = getattr(self._hot, "aclose", None)
        if hot_aclose is not None:
            await hot_aclose()

    async def _restore(self, *, draft_id: str) -> None:
        snapshot: DraftSnapshot = await self._cold.restore(draft_id=draft_id)
        await self._hot.hydrate(snapshot=snapshot)

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
