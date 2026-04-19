from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import TempoMarking

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class TempoChange(ContextNode):
    bpm: int
    marking: TempoMarking
