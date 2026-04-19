from dataclasses import dataclass

from piano_app.domain.score.models.graph.node import Node
from piano_app.domain.score.models.graph.notation import RhythmicValue


@dataclass(frozen=True, slots=True, kw_only=True)
class Carrier(Node):
    rhythmic_value: RhythmicValue
    dot_count: int = 0
