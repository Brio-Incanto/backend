from fractions import Fraction

from piano_app.domain.score.document.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.document.models.structural.rhythm.metric import (
    GroupRhythmicContainer,
    RhythmicContainer,
)
from piano_app.domain.score.document.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)

from .interval import Interval


def translate_to_root(
    *,
    interval: Interval,
) -> Interval:
    """Translate an interval from its current scope up to the voice-root scope."""
    current_scope: RhythmicContainerParent = interval.scope

    if isinstance(current_scope, Voice):
        return interval

    if isinstance(current_scope, GroupRhythmicContainer):
        return translate_to_root(
            interval=_project_into_parent(interval=interval, group=current_scope)
        )

    raise ValueError(f"Unexpected scope type: {type(current_scope).__name__}.")


def translate_to_deeper_scope(
    *,
    interval: Interval,
    target_scope: RhythmicContainerParent,
) -> Interval:
    """Translate an interval down into ``target_scope``, a descendant of its scope."""
    if interval.scope is target_scope:
        return interval

    if not isinstance(target_scope, GroupRhythmicContainer):
        raise ValueError("Target scope is not a descendant of the interval's scope.")

    # descend into the target's parent first, then one step into the target itself
    return _project_into_child(
        interval=translate_to_deeper_scope(
            interval=interval,
            target_scope=target_scope.parent,
        ),
        child=target_scope,
    )


def _project_into_parent(
    *,
    interval: Interval,
    group: GroupRhythmicContainer,
) -> Interval:
    """Project an interval from a group's interior into its parent scope (one level up)."""
    parent_interval: Interval = interval_in_parent_scope(container=group)
    # occupied / written = tuplet ratio
    extension_ratio: Fraction = group.occupied_size.fraction / group.written_size.fraction

    return Interval.of_span(
        scope=group.parent,
        start=(interval.start * extension_ratio) + parent_interval.start,
        length=interval.length * extension_ratio,
    )


def _project_into_child(
    *,
    interval: Interval,
    child: GroupRhythmicContainer,
) -> Interval:
    """Project an interval from a group's parent scope into its interior (one level down)."""
    child_interval: Interval = interval_in_parent_scope(container=child)
    # occupied / written = tuplet ratio
    extension_ratio: Fraction = child.occupied_size.fraction / child.written_size.fraction

    return Interval.of_span(
        scope=child,
        start=(interval.start - child_interval.start) / extension_ratio,
        length=interval.length / extension_ratio,
    )


def interval_in_parent_scope(
    *,
    container: RhythmicContainer,
) -> Interval:
    parent_scope: RhythmicContainerParent = container.parent

    # if parent is a voice, calculate based on container's anchor because it's global
    if isinstance(parent_scope, Voice):
        start_anchor: TemporalAnchor = container.start_anchor
        return Interval.of_span(
            scope=parent_scope,
            start=global_position(
                measure=start_anchor.measure,
                position=start_anchor.position,
            ),
            length=container.occupied_size.fraction,
        )

    # if parent is a group, calculate based on the group's children offsets
    if isinstance(parent_scope, GroupRhythmicContainer):
        current_offset: Fraction = Fraction(0)
        for child in parent_scope.children:
            if child is container:
                return Interval.of_span(
                    scope=parent_scope,
                    start=current_offset,
                    length=container.occupied_size.fraction,
                )
            current_offset += child.occupied_size.fraction

    raise ValueError(f"Unexpected parent scope type: {type(parent_scope).__name__}.")


def calculate_scope_ratio_up_to_root(
    *,
    start: RhythmicContainer,
) -> Fraction:
    """Product of the tuplet ratios (occupied / written) of every group enclosing
    ``start`` — the factor from ``start``'s own scope out to real (root) time."""
    parent: RhythmicContainerParent = start.parent
    if isinstance(parent, Voice):
        return Fraction(1)

    if isinstance(parent, GroupRhythmicContainer):
        ratio: Fraction = parent.occupied_size.fraction / parent.written_size.fraction
        return ratio * calculate_scope_ratio_up_to_root(start=parent)

    raise ValueError(f"Unexpected parent scope type: {type(parent).__name__}.")


def calculate_scope_ratio_up_to(
    *,
    start: RhythmicContainer,
    target: RhythmicContainerParent,
) -> Fraction:
    """Product of the tuplet ratios of the groups between ``start``'s scope and
    ``target`` (exclusive) — the factor from ``start``'s scope out to ``target``."""
    parent: RhythmicContainerParent = start.parent
    if parent is target:
        return Fraction(1)

    if isinstance(parent, Voice):
        raise ValueError("Target scope is unreachable from the start scope.")

    if isinstance(parent, GroupRhythmicContainer):
        ratio: Fraction = parent.occupied_size.fraction / parent.written_size.fraction
        return ratio * calculate_scope_ratio_up_to(start=parent, target=target)

    raise ValueError(f"Unexpected parent scope type: {type(parent).__name__}.")


def calculate_scope_ratio_down_to(
    *,
    start: RhythmicContainer,
    target: RhythmicContainer,
) -> Fraction:
    """Inverse of the up factor: from ``start``'s scope down into ``target``'s scope."""
    return Fraction(1) / calculate_scope_ratio_up_to(start=start, target=target.parent)


def measure_origin(*, measure: Measure) -> Fraction:
    """Return the measure's start on the global timeline.
    Calculates by summing the durations of all preceding measures.
    """
    total: Fraction = Fraction(0)

    previous: Measure | None = measure.prev_measure
    while previous is not None:
        total += previous.time_signature.fraction
        previous = previous.prev_measure

    return total


def global_position(*, measure: Measure, position: MeasurePosition) -> Fraction:
    """Return the measure local position on the global timeline.
    Calculates finding the measure's origin and adding the offset within the source measure.
    """
    return measure_origin(measure=measure) + position.value


def measure_global_interval(*, measure: Measure, voice: Voice) -> Interval:
    """Return the measure's interval on the global timeline."""
    return Interval.of_span(
        scope=voice,
        start=measure_origin(measure=measure),
        length=measure.time_signature.fraction,
    )


# inefficient due to n + 1
# global interval for each measure is calculated
# by finding the cumulative sum of all preceding without caching
def build_measure_interval_map(
    *,
    origin_measure: Measure,
    voice: Voice,
) -> dict[Measure, Interval]:
    measure_interval_map: dict[Measure, Interval] = {}

    # add all preceding measures to the map
    previous: Measure | None = origin_measure.prev_measure
    while previous is not None:
        measure_interval_map[previous] = measure_global_interval(measure=previous, voice=voice)
        previous = previous.prev_measure

    # add the origin measure to the map
    measure_interval_map[origin_measure] = measure_global_interval(
        measure=origin_measure, voice=voice
    )

    # add all following measures to the map
    following: Measure | None = origin_measure.next_measure
    while following is not None:
        measure_interval_map[following] = measure_global_interval(measure=following, voice=voice)
        following = following.next_measure

    return measure_interval_map
