from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import RhythmicValue

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class TimeSignatureChange(ContextNode):
    beats_per_measure: int
    beat_unit: RhythmicValue

    def __post_init__(self) -> None:
        if self.beats_per_measure < 1:
            raise ValueError("Beats per measure cannot be less than 1.")
