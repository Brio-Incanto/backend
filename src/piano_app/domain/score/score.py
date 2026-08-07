from dataclasses import dataclass
from datetime import datetime

from .document import ScoreDocument


@dataclass(slots=True, kw_only=True)
class Score:
    """A score model includes metadata and a document."""

    id: str
    title: str
    author_id: str
    composer: str | None = None
    derived_from_id: str | None = None
    is_public: bool = False
    document: ScoreDocument
    created_at: datetime
    updated_at: datetime
