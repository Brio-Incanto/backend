from dataclasses import dataclass
from enum import IntEnum
from fractions import Fraction


class RhythmicValue(IntEnum):
    WHOLE = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16
    THIRTY_SECOND = 32

    @property
    def fraction(self) -> Fraction:
        return Fraction(1, self.value)


# The shortest note; dots may not reach below it. (Members are ints, so this
# compares directly against a numeric "reach".)
_SMALLEST_NOTE: RhythmicValue = max(RhythmicValue)


@dataclass(frozen=True, slots=True, kw_only=True)
class DottedRhythmicValue:
    value: RhythmicValue
    dots_count: int = 0

    def __post_init__(self) -> None:
        if self.dots_count < 0:
            raise ValueError("Dots count cannot be negative.")

        # Each dot adds a note one step smaller; forbid dots that would reach
        # below the smallest note, since the resulting remainder could not be
        # filled by a rest.
        if self.value * 2**self.dots_count > _SMALLEST_NOTE:
            raise ValueError(
                f"{self.dots_count} dots on {self.value.name} reach below the smallest note value."
            )

    @property
    def fraction(self) -> Fraction:
        # Dotted duration is a geometric sum: base * (1 + 1/2 + ... + 1/2^dots).
        return self.value.fraction * (2 - Fraction(1, 2**self.dots_count))


@dataclass(frozen=True, slots=True, kw_only=True)
class RhythmicSize:
    value: DottedRhythmicValue
    count: int

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("Count cannot be less than 1.")

    @property
    def fraction(self) -> Fraction:
        return self.value.fraction * self.count
