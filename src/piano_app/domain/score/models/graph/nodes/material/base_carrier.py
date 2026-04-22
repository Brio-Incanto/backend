from dataclasses import dataclass

from piano_app.domain.score.models.graph.node import Node
from piano_app.domain.score.models.graph.notation import RhythmicValue


@dataclass(frozen=True, slots=True, kw_only=True)
class Carrier(Node):
    rhythmic_value: RhythmicValue
    dot_count: int = 0

    def __post_init__(self) -> None:
        if self.dot_count < 0:
            raise ValueError(
                "Dot count cannot be negative: augmentation dots start at 0."
            )
