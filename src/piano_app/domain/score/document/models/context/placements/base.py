from dataclasses import dataclass

from piano_app.domain.score.document.models.base import ScoreEntity


@dataclass(slots=True, kw_only=True, eq=False)
class ContextPlacement(ScoreEntity):
    pass
