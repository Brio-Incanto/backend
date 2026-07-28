from fractions import Fraction

from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    Voice,
)
from piano_app.domain.score.models.structural.rhythm.metric import (
    GroupRhythmicContainer,
    RhythmicContainer,
)
from piano_app.domain.score.models.structural.rhythm.metric.parent import RhythmicContainerParent

from piano_app.domain.score.services.helpers.primitives import Interval


# bottom up direction
def translate_to_root_scoped(
    to_translate: Interval,
) -> Interval:
    """Helper is used in order not to pass the voice to the recursion."""

    def _helper(
        *,
        interval: Interval,
    ) -> Interval:
        """Translate an interval from its current scope to the voice-root scope."""
        # current scope - relative to the parent
        # parent's scope - relative to the grandparent
        current_scope: RhythmicContainerParent = interval.scope

        # terminal case, voice reached that means that the interval is already global
        if isinstance(current_scope, Voice):
            return interval

        # find interval of parent in its own scope
        if isinstance(current_scope, GroupRhythmicContainer):
            parent_interval: Interval = interval_in_parent_scope(container=current_scope)

            # calculate coef between parent's occupied and written size
            extension_coef: Fraction = (
                current_scope.occupied_size.fraction / current_scope.written_size.fraction
            )
            # calculate the offset of parent in its scope
            offset: Fraction = parent_interval.start

            # apply coef and offset to the interval to project it into its parent's scope
            projected: Interval = Interval.of_span(
                scope=current_scope.parent,
                start=(interval.start * extension_coef) + offset,
                length=interval.length * extension_coef,
            )

            # recursively go up the parent hierarchy
            return _helper(interval=projected)

        raise TypeError("Rhythmic container parent type is not supported.")

    return _helper(interval=to_translate)


# top down direction
def translate_to_local(
    to_translate: Interval,
) -> Interval:
    """Helper is used in order not to pass the voice to the recursion."""

    def _helper(
        *,
        interval: Interval,
    ) -> Interval:
        """Search for the deepest scope that fully covers the interval."""
        current_scope: RhythmicContainerParent = interval.scope

        # iterate over all containers in the space
        for child in current_scope.children:
            # interval of child in the same scope
            child_interval: Interval = interval_in_parent_scope(container=child)

            # max one should contain the interval, so return after checking it
            if child_interval.contains(interval):
                if isinstance(child, GroupRhythmicContainer):
                    # calculate coef between container's occupied and written scope
                    extension_coef: Fraction = (
                        child.occupied_size.fraction / child.written_size.fraction
                    )

                    # calculate the offset of container in its scope
                    offset: Fraction = child_interval.start

                    # apply coef and offset to the interval to project it into its deeper scope
                    projected: Interval = Interval.of_span(
                        scope=child,
                        start=(interval.start - offset) / extension_coef,
                        length=interval.length / extension_coef,
                    )

                    return _helper(interval=projected)

                # if is contained not within a group but a leaf,
                # break the loop, there is nothing deeper
                break

        # terminal case, nothing deeper covers the interval
        return interval

    return _helper(interval=to_translate)


def interval_in_parent_scope(
    container: RhythmicContainer,
) -> Interval:
    raise NotImplementedError


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
