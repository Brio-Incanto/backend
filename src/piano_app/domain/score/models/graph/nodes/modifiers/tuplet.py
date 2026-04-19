from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import RhythmicValue

from .base import ModifierNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Tuplet(ModifierNode):
    actual_count: int
    original_count: int
    count_value: RhythmicValue
