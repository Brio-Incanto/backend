from dataclasses import dataclass

from .base import StructuralNode


@dataclass(frozen=True, slots=True, kw_only=True)
class TimePoint(StructuralNode):
    position_numerator: int
    position_denominator: int
