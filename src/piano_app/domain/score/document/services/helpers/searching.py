from fractions import Fraction

from piano_app.domain.score.document.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.document.models.structural.rhythm import (
    GroupRhythmicContainer,
    LeafRhythmicContainer,
    RhythmicContainer,
)
from piano_app.domain.score.document.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)
from piano_app.domain.score.document.services.helpers import voice_of
from piano_app.domain.score.document.services.helpers.interval import Interval
from piano_app.domain.score.document.services.helpers.scope import interval_in_parent_scope


def find_anchor_at(
    *,
    measure: Measure,
    position: MeasurePosition,
) -> TemporalAnchor | None:
    # one or None guaranteed in model
    return next(
        (anchor for anchor in measure.anchors if anchor.position == position),
        None,
    )


def find_leaf_of_voice_at_anchor(
    *,
    anchor: TemporalAnchor,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    # validate only one leaf container per voice at one anchor
    leaves: list[LeafRhythmicContainer] = [
        leaf for leaf in anchor.leaf_containers if voice_of(leaf) is voice
    ]
    if len(leaves) > 1:
        raise ValueError(f"Multiple leaf containers found for voice {voice} at one anchor.")

    # return this only leaf container or None
    return leaves[0] if leaves else None


def find_leaf_at(
    *,
    measure: Measure,
    position: MeasurePosition,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    anchor: TemporalAnchor | None = find_anchor_at(measure=measure, position=position)
    if anchor is None:
        return None

    return find_leaf_of_voice_at_anchor(
        anchor=anchor,
        voice=voice,
    )


def locate_in_deepest_scope(
    *,
    scope: RhythmicContainerParent,
    start: Fraction,
    written_length: Fraction,
) -> Interval:
    """Place a requested written interval in the deepest scope containing its start."""
    for child in scope.children:
        if not isinstance(child, GroupRhythmicContainer):
            continue

        child_interval: Interval = interval_in_parent_scope(container=child)
        if not child_interval.start <= start < child_interval.end:
            continue

        extension_ratio: Fraction = child.occupied_size.fraction / child.written_size.fraction
        local_start: Fraction = (start - child_interval.start) / extension_ratio

        return locate_in_deepest_scope(
            scope=child,
            start=local_start,
            written_length=written_length,
        )

    interval: Interval = Interval.of_span(
        scope=scope,
        start=start,
        length=written_length,
    )
    if isinstance(scope, GroupRhythmicContainer) and interval.end > scope.written_size.fraction:
        raise ValueError("Interval overlaps a group boundary.")

    return interval


def find_intersections(
    *,
    interval: Interval,
) -> list[RhythmicContainer]:
    intersecting_children: list[RhythmicContainer] = []
    for child in interval.scope.children:
        child_interval = interval_in_parent_scope(container=child)
        if interval.intersects(child_interval):
            intersecting_children.append(child)

    return intersecting_children


def find_measure_at_position(
    *,
    first_measure: Measure,
    position: Fraction,
) -> Measure:
    accumulated_size: Fraction = Fraction(0)

    current_measure: Measure | None = first_measure
    while current_measure is not None:
        accumulated_size += current_measure.time_signature.fraction
        if position < accumulated_size:
            return current_measure

        current_measure = current_measure.next_measure

    raise ValueError(f"Position {position} is outside of the score.")
