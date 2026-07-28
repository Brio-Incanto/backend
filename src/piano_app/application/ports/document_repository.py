from typing import Protocol

from piano_app.domain.score.models import ScoreDocument


class DocumentRepository(Protocol):
    """Provides access to the score document being edited."""

    def get(self) -> ScoreDocument: ...
