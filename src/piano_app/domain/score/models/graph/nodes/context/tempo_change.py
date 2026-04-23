from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import TempoMarking

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class TempoChange(ContextNode):
    bpm: int
    marking: TempoMarking

    def __post_init__(self) -> None:
        if self.bpm < 1:
            raise ValueError("Tempo must be at least 1 BPM.")
