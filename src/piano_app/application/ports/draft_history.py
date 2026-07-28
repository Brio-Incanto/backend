from typing import Protocol

from piano_app.domain.score.models import ScoreDocument

from .draft_store import DraftStore


class DraftHistory(DraftStore, Protocol):
    """An extension of the draft store that also supports interaction with
    the recorded history by adding new entries to it by committing drafts
    or undoing/redoing them.
    """

    def undo(self, *, draft_id: str) -> bool:
        """Rolls back the most recent gesture.
        Returns ``False`` if there is nothing to undo.
        """
        ...

    def redo(self, *, draft_id: str) -> bool:
        """Reapplies the most recently undone gesture.
        Returns ``False`` if there is nothing to redo.
        """
        ...

    def commit(self, *, draft_id: str, document: ScoreDocument) -> None: ...
