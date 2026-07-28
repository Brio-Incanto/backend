from piano_app.application.errors import DraftNotFoundError
from piano_app.domain.score.models import ScoreDocument


class InMemoryDraftStore:
    """In-process draft store keyed by draft id."""

    def __init__(self, *, drafts: dict[str, ScoreDocument] | None = None) -> None:
        self._drafts: dict[str, ScoreDocument] = dict(drafts) if drafts is not None else {}

    def load(self, *, draft_id: str) -> ScoreDocument:
        document: ScoreDocument | None = self._drafts.get(draft_id)
        if document is None:
            raise DraftNotFoundError(draft_id=draft_id)

        return document

    def save(self, *, draft_id: str, document: ScoreDocument) -> None:
        self._drafts[draft_id] = document
