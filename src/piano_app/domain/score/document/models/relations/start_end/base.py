from dataclasses import dataclass

from piano_app.domain.score.document.models import ScoreEntity
from piano_app.domain.score.document.models.relations.base import Relation
from piano_app.domain.shared.abstract import abstract


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class StartEndRelation[T: ScoreEntity](Relation):
    start: T
    end: T

    def __post_init__(self) -> None:
        if self.start is self.end:
            raise ValueError("Start and end must be different entities.")
