from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction

from .coordinates import Point, Span
from .errors import FrameMismatchError
from .frame import Frame


@dataclass(frozen=True, slots=True, kw_only=True)
class Meeting[T]:
    """One region a span reaches into, and the part they share.

    ``part`` is expressed in the query span's frame, so a caller can act on the
    pieces without projecting anything back.
    """

    region: T
    part: Span


def meetings[T](*, span: Span, candidates: Iterable[tuple[T, Span]]) -> list[Meeting[T]]:
    """Which of ``candidates`` the span reaches into, left to right.

    THE unified primitive. Cutting at barlines, finding what a new container
    displaces, and descending into a nested group are the same question — a span
    against a set of sibling regions — and differ only in what the caller keeps:
    every piece (slicing), the regions alone (displacement), or the single region
    holding the start (descent).

    Reaching across a boundary is reported, never refused: whether that means slice,
    reject, or join is a decision this layer has no business making.
    """
    met: list[Meeting[T]] = []
    for region, region_span in candidates:
        part: Span | None = span.intersection(region_span)
        if part is not None:
            met.append(Meeting(region=region, part=part))

    return sorted(met, key=lambda meeting: meeting.part.start)


def containing[T](*, point: Point, candidates: Iterable[tuple[T, Span]]) -> T | None:
    """The one region holding the point, or ``None`` when it falls between them.

    Half-open, so a point sitting exactly on a boundary belongs to the region that
    starts there — the same rule ``Span`` uses, kept consistent so a position never
    lands in two places at once.
    """
    for region, region_span in candidates:
        if point.frame != region_span.frame:
            raise FrameMismatchError("Cannot locate a point among regions of another frame.")

        if region_span.start <= point.value < region_span.end:
            return region

    return None


def footprint(*, frame: Frame) -> Span:
    """The room a frame takes up in its parent.

    Derived from the step itself, which is what makes a measure and a tuplet group
    answerable by one call: a measure's footprint is its own length (it does not
    compress), a group's is its written interior after squeezing — its occupied size.
    """
    parent: Frame | None = frame.parent
    if parent is None:
        raise ValueError("The root frame has no parent to take up room in.")

    extent: Fraction | None = frame.extent
    if extent is None:
        raise ValueError("An unbounded frame has no footprint.")

    return Span(
        frame=parent,
        start=frame.to_parent.apply_position(Fraction(0)),
        length=frame.to_parent.apply_length(extent),
    )


def interior(*, frame: Frame) -> Span:
    """The frame's whole space, in its OWN coordinates.

    The inward-facing counterpart of ``footprint``: same region, seen from inside
    rather than from the parent.
    """
    extent: Fraction | None = frame.extent
    if extent is None:
        raise ValueError("An unbounded frame has no bounded interior.")

    return Span(frame=frame, start=Fraction(0), length=extent)


def overflow(*, span: Span) -> Fraction:
    """How far the span reaches past its own frame — zero when it fits.

    Returned as a number rather than raised: a span that outgrows a group is a fact
    the caller weighs (reject it, slice it, grow the group), not an error here.
    """
    extent: Fraction | None = span.frame.extent
    if extent is None:
        return Fraction(0)

    return max(Fraction(0), span.end - extent)


def gaps(*, bucket: Span, covered: Sequence[Span]) -> list[Span]:
    """What is left uncovered inside ``bucket``.

    Says nothing about whether those holes ought to be filled — a region nobody
    covers at all still reports as one whole gap, and it is the caller who decides
    that such a region is asleep rather than empty.
    """
    return bucket.remainder_after(list(covered))
