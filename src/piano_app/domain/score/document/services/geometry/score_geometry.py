from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.document.models.structural import Measure, TemporalAnchor, Voice
from piano_app.domain.score.document.models.structural.rhythm import (
    GroupRhythmicContainer,
    RhythmicContainer,
    RhythmicContainerParent,
)

from .coordinates import Point, Span
from .frame import Frame, RootFrame
from .queries import Meeting, containing, footprint, meetings
from .transform import Transform

# This module is the ONLY place in `geometry` that knows the score model exists.
# Everything else works on frames alone, which is what keeps the mechanism testable
# without a document and reusable for spaces we have not invented yet.


def _head_measure(*, measure: Measure) -> Measure:
    """The first measure of the chain — the token that identifies one timeline.

    Reachable from ANY measure, which is what lets an analyzer holding nothing but
    its own measure build a bridge whose coordinates combine with everyone else's.
    """
    head: Measure = measure
    while head.prev_measure is not None:
        head = head.prev_measure

    return head


def _measure_origin(*, measure: Measure) -> Fraction:
    """Where the measure begins on the global timeline — the sum of everything
    before it. Measures shift, they never compress."""
    total: Fraction = Fraction(0)

    previous: Measure | None = measure.prev_measure
    while previous is not None:
        total += previous.time_signature.fraction
        previous = previous.prev_measure

    return total


def _anchor_position(*, anchor: TemporalAnchor) -> Fraction:
    return _measure_origin(measure=anchor.measure) + anchor.position.value


def _offset_in_parent(*, container: RhythmicContainer) -> Fraction:
    """Where the container begins inside its parent frame.

    Never stored: inserting a sibling shifts everything to its right, so a cached
    offset would be stale after every edit. Derived live instead.
    """
    parent: RhythmicContainerParent = container.parent

    # inside a group, position is the room the earlier siblings already take
    if isinstance(parent, GroupRhythmicContainer):
        offset: Fraction = Fraction(0)
        for child in parent.children:
            if child is container:
                return offset

            offset += child.occupied_size.fraction

        raise ValueError("Container is not among its parent's children.")

    # otherwise it sits on the global timeline, located by its own anchor
    if isinstance(parent, Voice):
        return _anchor_position(anchor=container.start_anchor)

    raise TypeError(f"Parent is not a voice or a group: {parent!r}")


def _frame_of_scope(*, scope: RhythmicContainerParent, root: RootFrame) -> Frame:
    """The coordinate space a parent stands for.

    The single place in the whole geometry stack that asks what kind of parent it is
    looking at — translating a model shape into a frame is exactly this module's job,
    and everything above it works on frames alone.
    """
    if isinstance(scope, GroupRhythmicContainer):
        return _GroupFrame(source=scope, root=root)

    # a voice owns a set of children but is not a coordinate space of its own — it
    # has no extent and compresses nothing, so its containers sit directly on the
    # global timeline
    if isinstance(scope, Voice):
        return root

    raise TypeError(f"Scope is not a voice or a group: {scope!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class _MeasureFrame:
    """A measure as a coordinate space: the degenerate frame that shifts without
    compressing."""

    source: Measure
    root: RootFrame

    @property
    def parent(self) -> RootFrame:
        return self.root

    @property
    def to_parent(self) -> Transform:
        return Transform.of_shift(offset=_measure_origin(measure=self.source))

    @property
    def extent(self) -> Fraction:
        return self.source.time_signature.fraction


@dataclass(frozen=True, slots=True, kw_only=True)
class _GroupFrame:
    """A tuplet group as a coordinate space — its written interior, squeezed into the
    room it occupies outside."""

    source: GroupRhythmicContainer
    root: RootFrame

    @property
    def parent(self) -> Frame:
        return _frame_of_scope(scope=self.source.parent, root=self.root)

    @property
    def to_parent(self) -> Transform:
        return Transform.of_nesting(
            written=self.source.written_size.fraction,
            occupied=self.source.occupied_size.fraction,
            offset=_offset_in_parent(container=self.source),
        )

    @property
    def extent(self) -> Fraction:
        return self.source.written_size.fraction


class ScoreGeometry:
    """Reads the live score as frames.

    Stateless beyond the timeline it stands for: every coordinate is
    derived on access, so nothing here can go stale while the engine mutates the
    model mid-gesture.
    """

    def __init__(self, *, origin: Measure) -> None:
        # keyed on the head of the chain, not on the document: an analyzer only ever
        # holds a measure, and both routes must agree or their coordinates would not
        # combine
        self._head: Measure = _head_measure(measure=origin)
        self._root: RootFrame = RootFrame(owner=self._head)

    @property
    def root(self) -> Frame:
        """The global timeline both measures and rhythm project into."""
        return self._root

    def of_measure(self, *, measure: Measure) -> Frame:
        return _MeasureFrame(source=measure, root=self._root)

    def of_group(self, *, group: GroupRhythmicContainer) -> Frame:
        return _GroupFrame(source=group, root=self._root)

    def of_scope(self, *, scope: RhythmicContainerParent) -> Frame:
        """The space a voice or a group stands for."""
        return _frame_of_scope(scope=scope, root=self._root)

    def containing_frame_of(self, *, container: RhythmicContainer) -> Frame:
        """The space the container LIVES IN, its parent frame. A leaf has no
        interior of its own, so this is the only frame it ever relates to."""
        return _frame_of_scope(scope=container.parent, root=self._root)

    def span_of(self, *, container: RhythmicContainer) -> Span:
        """The room the container takes in its parent frame.

        A group answers this with its ``occupied_size`` while its own interior
        measures ``written_size`` — the two halves of being both a frame and placed.
        """
        return Span(
            frame=_frame_of_scope(scope=container.parent, root=self._root),
            start=_offset_in_parent(container=container),
            length=container.occupied_size.fraction,
        )

    def global_span_of(self, *, container: RhythmicContainer) -> Span:
        """The container's room on the global timeline — the one call that replaces
        hand-assembling a parent-scope lookup with a walk up to the root."""
        return self.span_of(container=container).to(frame=self._root)

    def point_of(self, *, anchor: TemporalAnchor) -> Point:
        """An anchor's location on the global timeline."""
        return Point(frame=self._root, value=_anchor_position(anchor=anchor))

    def contents_of(
        self,
        *,
        scope: RhythmicContainerParent,
    ) -> list[tuple[RhythmicContainer, Span]]:
        """What sits in a scope, ready to be handed to ``meetings`` / ``containing``."""
        return [(child, self.span_of(container=child)) for child in scope.children]

    def measure_regions(self) -> list[tuple[Measure, Span]]:
        """The measures as regions of the global timeline, in order."""
        regions: list[tuple[Measure, Span]] = []

        measure: Measure | None = self._head
        while measure is not None:
            regions.append((measure, footprint(frame=self.of_measure(measure=measure))))
            measure = measure.next_measure

        return regions

    def measure_at(self, *, point: Point) -> Measure | None:
        """Which measure holds the point, or ``None`` past the end of the score.

        ``None`` rather than an error: running off the end is something the caller
        answers for (reject the edit, append a measure), not a geometric impossibility.
        """
        return containing(point=point.to(frame=self._root), candidates=self.measure_regions())

    def slice_by_measures(self, *, span: Span) -> list[Meeting[Measure]]:
        """Cut a span at the barlines it crosses.

        Returns every piece; a single piece means it stayed inside one measure. What
        to do with more than one — tie them together, refuse the edit — is the
        caller's call, which is why this reports instead of rejecting.
        """
        return meetings(span=span.to(frame=self._root), candidates=self.measure_regions())

    def intersecting(
        self,
        *,
        span: Span,
        scope: RhythmicContainerParent,
    ) -> list[Meeting[RhythmicContainer]]:
        """What already sits where the span wants to go."""
        return meetings(span=span, candidates=self.contents_of(scope=scope))

    def deepest_scope_at(
        self,
        *,
        point: Point,
        voice: Voice,
    ) -> tuple[RhythmicContainerParent, Point]:
        """Descend to the innermost space holding the point, restating it on the way.

        Returns the scope AND the point in that scope's coordinates, so the caller can
        build a span there directly. Nothing is rejected: a requested size that will
        not fit the scope it lands in is reported by ``overflow`` afterwards, and what
        that means is the caller's to decide.
        """
        scope: RhythmicContainerParent = voice
        local: Point = point.to(frame=self._root)

        while True:
            nested: list[tuple[GroupRhythmicContainer, Span]] = [
                (child, self.span_of(container=child))
                for child in scope.children
                if isinstance(child, GroupRhythmicContainer)
            ]

            entered: GroupRhythmicContainer | None = containing(point=local, candidates=nested)
            if entered is None:
                return scope, local

            scope = entered
            local = local.to(frame=self.of_group(group=entered))
