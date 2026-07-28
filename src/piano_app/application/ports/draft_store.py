from typing import Protocol

from piano_app.domain.score.models import ScoreDocument


class DraftNotFoundError(Exception):
    """Raised by a ``DraftStore``/``DraftHistory`` implementation when a draft id has
    no working copy."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id = draft_id


class DraftStore(Protocol):
    """Holds the transient working copy (draft) of each editing session, keyed by
    draft id.

    Drafts are either branches from existing scores or a completely new score
    branched from an empty document.
    The interface of this store is intended to work with already existing drafts.
    """

    def load(self, *, draft_id: str) -> ScoreDocument:
        """Raises ``DraftNotFoundError`` if ``draft_id`` has no working copy."""
        ...
