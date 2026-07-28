from collections.abc import Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from piano_app.domain.score.models.context.placements import (
        ContextPlacement,
        SpanContextPlacement,
    )
    from piano_app.domain.score.models.structural.measure import Measure
    from piano_app.domain.score.models.structural.rhythm.metric import (
        LeafRhythmicContainer,
    )


@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class MeasurePosition:
    # value is measured in whole notes (whole = 1).
    # it is a default unit in the system.
    value: Fraction

    def __post_init__(self) -> None:
        # validity of the position itself.
        # compatibility with a measure is checked
        # when adding the anchor with this position to a measure.
        if self.value < 0:
            raise ValueError("Measure position cannot be negative.")

    @classmethod
    def of(cls, *, numerator: int, denominator: int) -> MeasurePosition:
        return cls(value=Fraction(numerator, denominator))

    @classmethod
    def of_fraction(cls, *, fraction: Fraction) -> MeasurePosition:
        return cls(value=fraction)


@dataclass(slots=True, kw_only=True, eq=False)
class TemporalAnchor(ScoreEntity):
    position: MeasurePosition
    _measure: Measure

    _leaf_containers: list[LeafRhythmicContainer] = field(default_factory=list)

    _starting_contexts: list[ContextPlacement] = field(default_factory=list)
    _ending_contexts: list[SpanContextPlacement] = field(default_factory=list)

    @property
    def measure(self) -> Measure:
        return self._measure

    @property
    def leaf_containers(self) -> Sequence[LeafRhythmicContainer]:
        return self._leaf_containers

    @property
    def starting_contexts(self) -> Sequence[ContextPlacement]:
        return self._starting_contexts

    @property
    def ending_contexts(self) -> Sequence[SpanContextPlacement]:
        return self._ending_contexts

    @property
    def is_orphan(self) -> bool:
        return (
            not self._leaf_containers and not self._starting_contexts and not self._ending_contexts
        )

    @classmethod
    def create(
        cls,
        *,
        measure: Measure,
        position: MeasurePosition,
        sink: MutationSink = DIRECT_SINK,
    ) -> TemporalAnchor:
        anchor: TemporalAnchor = cls(
            position=position,
            _measure=measure,
        )

        anchor.attach(sink=sink)
        return anchor

    def attach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._measure.add_anchor(anchor=self, sink=sink)

    def detach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._measure.remove_anchor(anchor=self, sink=sink)

    def precedes(self, other: TemporalAnchor) -> bool:
        """Whether this anchor comes strictly before ``other`` on the timeline —
        an earlier measure, or the same measure at an earlier position."""
        if self._measure is other._measure:
            return self.position < other.position

        return self._measure.precedes(other._measure)

    def precedes_or_equals_position(
        self,
        *,
        measure: Measure,
        position: MeasurePosition,
    ) -> bool:
        if self._measure.precedes(measure):
            return True

        return self._measure is measure and self.position <= position

    def add_leaf_container(
        self,
        *,
        leaf_container: LeafRhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if leaf_container.anchor is not self:
            raise ValueError("Cannot add leaf container bound to a different anchor.")

        if leaf_container in self._leaf_containers:
            return

        sink.list_append(self._leaf_containers, leaf_container)

    def remove_leaf_container(
        self,
        *,
        leaf_container: LeafRhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if leaf_container.anchor is not self:
            raise ValueError("Cannot remove leaf container bound to a different anchor.")

        if leaf_container not in self._leaf_containers:
            return

        sink.list_remove(self._leaf_containers, leaf_container)
