from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.models.structural.rhythm.metric.parent import RhythmicContainerParent


@dataclass(frozen=True, slots=True, kw_only=True)
class Interval:
    """A half-open segment [start, end) in one rhythmic scope.
    Both start and end represent a position measured in units (1 unit = 1 whole note).
    Scope is validated on every operation between multiple intervals.
    """

    scope: RhythmicContainerParent

    start: Fraction
    end: Fraction

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("Interval start cannot be negative.")
        if self.end <= self.start:
            raise ValueError("Interval end must be greater than its start.")

    @classmethod
    def of_span(
        cls,
        *,
        scope: RhythmicContainerParent,
        start: Fraction,
        length: Fraction,
    ) -> Interval:
        """Build from a starting position and a length (a position + size)."""
        return cls(scope=scope, start=start, end=start + length)

    @classmethod
    def of_bounds(
        cls,
        *,
        scope: RhythmicContainerParent,
        start: Fraction,
        end: Fraction,
    ) -> Interval:
        """Build from a starting and ending position."""
        return cls(scope=scope, start=start, end=end)

    @property
    def length(self) -> Fraction:
        return self.end - self.start

    def intersects(self, other: Interval) -> bool:
        """True if the two segments overlap.
        Touching endpoints ([0, 1) and [1, 2)) do not count as an overlap.
        """
        self._validate_scope(other=other)
        return self.start < other.end and other.start < self.end

    def starts_inside(self, other: Interval) -> bool:
        """True if the interval starts inside the other interval."""
        self._validate_scope(other=other)
        return other.start <= self.start < other.end

    def ends_inside(self, other: Interval) -> bool:
        """True if the interval ends inside the other interval."""
        self._validate_scope(other=other)
        return other.start < self.end <= other.end

    def contains(self, other: Interval) -> bool:
        """True if ``other`` lies fully within this interval (bounds inclusive)."""
        self._validate_scope(other=other)
        return self.start <= other.start and other.end <= self.end

    def intersection(self, other: Interval) -> Interval | None:
        """Return the common part of this interval and ``other``.
        If the intervals do not overlap, return None.
        """
        self._validate_scope(other=other)
        if not self.intersects(other):
            return None

        return Interval(
            scope=self.scope, start=max(self.start, other.start), end=min(self.end, other.end)
        )

    def subtract(self, other: Interval) -> list[Interval]:
        """Return parts of this interval left uncovered by ``other``."""
        self._validate_scope(other=other)
        if not self.intersects(other):
            return [self]

        pieces: list[Interval] = []
        if self.start < other.start:
            pieces.append(Interval(scope=self.scope, start=self.start, end=other.start))
        if other.end < self.end:
            pieces.append(Interval(scope=self.scope, start=other.end, end=self.end))

        return pieces

    def subtract_many(self, others: list[Interval]) -> list[Interval]:
        """The parts of this interval left uncovered by the union of ``others``.
        Returns the pieces left-to-right (empty if ``others`` fully cover this interval).
        Overlapping or unsorted ``others`` are handled (merged by a left-to-right sweep).
        """
        self._validate_many_scopes(others=others)
        covering: list[Interval] = sorted(
            (other for other in others if self.intersects(other)),
            key=lambda other: other.start,
        )

        pieces: list[Interval] = []
        cursor: Fraction = self.start
        for other in covering:
            if other.start > cursor:
                pieces.append(Interval(scope=self.scope, start=cursor, end=other.start))

            # protect if we have two overlapping intervals in covering
            # and the end of current is before the end of the previous
            cursor = max(cursor, other.end)
            if cursor >= self.end:
                break

        if cursor < self.end:
            pieces.append(Interval(scope=self.scope, start=cursor, end=self.end))

        return pieces

    def _validate_scope(self, *, other: Interval) -> None:
        if self.scope is not other.scope:
            raise ValueError(
                "Cannot perform operation on intervals that are not in the same scope."
            )

    def _validate_many_scopes(self, *, others: list[Interval]) -> None:
        for other in others:
            self._validate_scope(other=other)
