from typing import Protocol

from piano_app.domain.score.models import ScoreDocument


class DraftStore(Protocol):
    """Holds the transient working copy (draft) of each editing session, keyed by
    draft id.

    Drafts are either branches from existing scores or a completely new score
    branched from an empty document.
    The interface of this store is intended to work with already existing drafts
    and to save transient changes to cache, not persist them.
    """

    def load(self, *, draft_id: str) -> ScoreDocument: ...

    def save(self, *, draft_id: str, document: ScoreDocument) -> None: ...
