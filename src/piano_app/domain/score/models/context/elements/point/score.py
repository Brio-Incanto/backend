from dataclasses import dataclass

from piano_app.domain.score.models.context.elements.base import ContextElement
from piano_app.domain.score.models.notation import TempoMarking


@dataclass(slots=True, kw_only=True, eq=False)
class ScorePointContextElement(ContextElement):
    pass


@dataclass(slots=True, kw_only=True, eq=False)
class TempoChange(ScorePointContextElement):
    bpm: int
    marking: TempoMarking

    def __post_init__(self) -> None:
        if self.bpm < 1:
            raise ValueError("Tempo must be at least 1 BPM.")
