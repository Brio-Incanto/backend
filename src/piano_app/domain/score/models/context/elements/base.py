from dataclasses import dataclass

from piano_app.domain.score.models.base import ScoreEntity

# potentially more layered abstraction


@dataclass(slots=True, kw_only=True, eq=False)
class ContextElement(ScoreEntity):
    pass
