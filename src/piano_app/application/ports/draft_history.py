from typing import Protocol

from .draft_store import DraftStore, VersionedDraftDocument


class DraftHistory(DraftStore, Protocol):
    """An extension of the draft store that also supports interaction with
    the recorded history by adding new entries to it by committing drafts
    or undoing/redoing them.
    """

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        """Rolls back the most recent gesture.

        ``draft.version`` is the version the caller loaded. Raises
        ``DraftVersionClashError`` if the draft has changed since then.
        Returns ``False`` if there is nothing to undo.
        """
        ...

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        """Reapplies the most recently undone gesture.

        ``draft.version`` is the version the caller loaded. Raises
        ``DraftVersionClashError`` if the draft has changed since then.
        Returns ``False`` if there is nothing to redo.
        """
        ...

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        """Commits a revision if ``draft.version`` is still current.

        Raises ``DraftVersionClashError`` if the draft has changed since it was loaded.
        """
        ...
