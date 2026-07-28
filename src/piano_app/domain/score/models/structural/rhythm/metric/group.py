from dataclasses import dataclass
from fractions import Fraction

from .base import RhythmicContainer


@dataclass(slots=True, kw_only=True)
class GroupRhythmicContainer(RhythmicContainer):
    children: list[RhythmicContainer]

    def __post_init__(self) -> None:
        if not self.children:
            raise ValueError("GroupRhythmicContainer must contain at least one child.")

        occupied_children_size: Fraction = sum(
            (child.occupied_size.fraction for child in self.children),
            Fraction(0, 1),
        )

        if occupied_children_size > self.written_size.fraction:
            raise ValueError(
                "GroupRhythmicContainer cannot contain children whose occupied "
                "size exceeds its written size."
            )
