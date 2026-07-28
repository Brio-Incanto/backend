from typing import Protocol

from piano_app.domain.score.models import ScoreDocument


class DraftStore(Protocol):
    """Holds the transient working copy (draft) of each editing session, keyed by
    draft id.

    A draft is unsaved editor state over a base (an existing revision or empty);
    it is committed to the persistent catalog only on save (future). The contract
    is explicit ``load`` / ``save`` — never "hand back the live object you mutate"
    — so an out-of-process implementation (e.g. Redis, deserialize on load,
    serialize on save) drops in behind the same port. The engine mutates the loaded
    document in place, so the caller must always ``save`` after a successful gesture.
    """

    def load(self, *, draft_id: str) -> ScoreDocument: ...

    def save(self, *, draft_id: str, document: ScoreDocument) -> None: ...
