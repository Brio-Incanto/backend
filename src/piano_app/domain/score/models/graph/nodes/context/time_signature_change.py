from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import RhythmicValue

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class TimeSignatureChange(ContextNode):
    beats_per_measure: int
    beat_unit: RhythmicValue
