from dataclasses import dataclass
from fractions import Fraction

from .errors import FrameMismatchError, OutsideFrameError
from .frame import Frame, conversion
from .transform import Transform


def _require_same_frame(*, left: Frame, right: Frame) -> None:
    # equality, not identity: frame adapters over the live model are built on demand,
    # so one space is many short-lived objects
    if left != right:
        raise FrameMismatchError("Cannot combine coordinates of different frames.")


def _require_inside(*, frame: Frame, start: Fraction, end: Fraction) -> None:
    """A projected coordinate must actually land in the space it was projected into.

    The end bound is inclusive: a span that exactly fills its frame ends on the
    boundary, and that is a legitimate coordinate rather than an overflow.
    """
    if start < 0:
        raise OutsideFrameError(f"Coordinate {start} lies before the frame.")

    extent: Fraction | None = frame.extent
    if extent is not None and end > extent:
        raise OutsideFrameError(f"Coordinate {end} lies past the frame's extent {extent}.")


@dataclass(frozen=True, slots=True, kw_only=True)
class Duration:
    """A displacement inside one frame — a length, never a location.

    Kept apart from ``Point`` on purpose: a duration transforms by scale alone,
    so offsetting one is meaningless and, with these as distinct types, also
    unrepresentable.
    """

    frame: Frame
    value: Fraction

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Duration cannot be negative.")

    def to(self, *, frame: Frame) -> Duration:
        """Restate this length in another frame — scale only, no placement involved,
        so this needs no containment check and no offset lookup."""
        if frame == self.frame:
            return self

        transform: Transform = conversion(source=self.frame, target=frame)

        return Duration(frame=frame, value=transform.apply_length(self.value))


@dataclass(frozen=True, slots=True, kw_only=True)
class Point:
    """A location inside one frame.

    Transforms affinely: every enclosing frame contributes both its compression and
    its own offset, and each of those offsets is itself compressed by everything
    above it — which is why a position cannot be rescaled by a single ratio the way
    a ``Duration`` can.
    """

    frame: Frame
    value: Fraction

    def to(self, *, frame: Frame) -> Point:
        """Restate this location in another frame.

        Raises ``OutsideFrameError`` when the point does not fall into the target —
        asking where a point sits in a space it never enters has no answer.
        """
        if frame == self.frame:
            return self

        transform: Transform = conversion(source=self.frame, target=frame)
        value: Fraction = transform.apply_position(self.value)
        _require_inside(frame=frame, start=value, end=value)

        return Point(frame=frame, value=value)

    def shifted_by(self, *, duration: Duration) -> Point:
        _require_same_frame(left=self.frame, right=duration.frame)

        return Point(frame=self.frame, value=self.value + duration.value)

    def distance_to(self, *, other: Point) -> Duration:
        """The displacement between two locations — the operation that turns a pair
        of points into a length."""
        _require_same_frame(left=self.frame, right=other.frame)

        return Duration(frame=self.frame, value=abs(other.value - self.value))


@dataclass(frozen=True, slots=True, kw_only=True)
class Span:
    """A half-open region ``[start, start + length)`` inside one frame — a ``Point``
    paired with a ``Duration``."""

    frame: Frame
    start: Fraction
    length: Fraction

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Span length must be positive.")

    @classmethod
    def between(cls, *, start: Point, end: Point) -> Span:
        _require_same_frame(left=start.frame, right=end.frame)

        return cls(frame=start.frame, start=start.value, length=end.value - start.value)

    @property
    def end(self) -> Fraction:
        return self.start + self.length

    @property
    def start_point(self) -> Point:
        return Point(frame=self.frame, value=self.start)

    @property
    def end_point(self) -> Point:
        return Point(frame=self.frame, value=self.end)

    @property
    def duration(self) -> Duration:
        return Duration(frame=self.frame, value=self.length)

    def to(self, *, frame: Frame) -> Span:
        """Restate this region in another frame.

        Raises ``OutsideFrameError`` when the region does not fit the target. A span
        that is EXPECTED to cross a barline or a group boundary should not be forced
        into one frame — ask what it meets instead, and decide from that.
        """
        if frame == self.frame:
            return self

        transform: Transform = conversion(source=self.frame, target=frame)
        start: Fraction = transform.apply_position(self.start)
        length: Fraction = transform.apply_length(self.length)
        _require_inside(frame=frame, start=start, end=start + length)

        return Span(frame=frame, start=start, length=length)

    def intersects(self, other: Span) -> bool:
        """Whether the two regions overlap. Touching ends ([0,1) and [1,2)) do not."""
        _require_same_frame(left=self.frame, right=other.frame)

        return self.start < other.end and other.start < self.end

    def intersection(self, other: Span) -> Span | None:
        """The common part, or ``None`` when they do not overlap."""
        _require_same_frame(left=self.frame, right=other.frame)
        if not self.intersects(other):
            return None

        start: Fraction = max(self.start, other.start)
        end: Fraction = min(self.end, other.end)

        return Span(frame=self.frame, start=start, length=end - start)

    def remainder_after(self, others: list[Span]) -> list[Span]:
        """The parts left uncovered by the union of ``others``, left to right.

        Overlapping or unsorted input is handled by the sweep, and an empty result
        means the region is fully covered.
        """
        for other in others:
            _require_same_frame(left=self.frame, right=other.frame)

        covering: list[Span] = sorted(
            (other for other in others if self.intersects(other)),
            key=lambda other: other.start,
        )

        pieces: list[Span] = []
        cursor: Fraction = self.start
        for other in covering:
            if other.start > cursor:
                pieces.append(Span(frame=self.frame, start=cursor, length=other.start - cursor))

            # guard the case of two overlapping covers where the current one ends
            # before the previous already reached
            cursor = max(cursor, other.end)
            if cursor >= self.end:
                break

        if cursor < self.end:
            pieces.append(Span(frame=self.frame, start=cursor, length=self.end - cursor))

        return pieces
