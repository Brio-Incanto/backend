from piano_app.domain.score.models import ScoreDocument


class InMemoryDocumentRepository:
    """Holds a single in-process score document (one editing session)."""

    def __init__(self, *, document: ScoreDocument) -> None:
        self._document = document

    def get(self) -> ScoreDocument:
        return self._document
