import math
from dataclasses import dataclass

from .base import StructuralNode


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasurePosition:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator < 0:
            raise ValueError("Measure position numerator cannot be negative.")

        if self.denominator < 1:
            raise ValueError(
                "Measure position denominator must be a positive subdivision."
            )

        if self.numerator > self.denominator:
            raise ValueError(
                "Measure position cannot lie beyond the end of the measure."
            )

    def __add__(self, other: MeasurePosition) -> MeasurePosition:
        lcm: int = math.lcm(self.denominator, other.denominator)

        normalized_self: int = self.numerator * (lcm // self.denominator)
        normalized_other: int = other.numerator * (lcm // other.denominator)

        return MeasurePosition(
            numerator=normalized_self + normalized_other,
            denominator=lcm,
        )

    def __lt__(self, other: MeasurePosition) -> bool:
        lcm: int = math.lcm(self.denominator, other.denominator)

        normalized_self: int = self.numerator * (lcm // self.denominator)
        normalized_other: int = other.numerator * (lcm // other.denominator)

        return normalized_self < normalized_other

    def __le__(self, other: MeasurePosition) -> bool:
        return self < other or self == other

    def __gt__(self, other: MeasurePosition) -> bool:
        return not self <= other

    def __ge__(self, other: MeasurePosition) -> bool:
        return not self < other


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasureTimePoint(StructuralNode):
    position: MeasurePosition
