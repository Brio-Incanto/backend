from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import RhythmicSize

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural.temporal_anchor import (
        TemporalAnchor,
    )


@dataclass(slots=True, kw_only=True, eq=False)
class Measure(ScoreEntity):
    time_signature: RhythmicSize
    _anchors: list[TemporalAnchor] = field(default_factory=list)

    _prev_measure: Measure | None = None
    _next_measure: Measure | None = None

    @property
    def anchors(self) -> Sequence[TemporalAnchor]:
        return self._anchors

    @property
    def prev_measure(self) -> Measure | None:
        return self._prev_measure

    @property
    def next_measure(self) -> Measure | None:
        return self._next_measure

    @classmethod
    def create(
        cls,
        *,
        time_signature: RhythmicSize,
    ) -> Measure:
        return cls(time_signature=time_signature)

    def set_next(self, *, next_measure: Measure | None, sink: MutationSink = DIRECT_SINK) -> None:
        sink.set_field(self, "_next_measure", next_measure)

    def set_prev(self, *, prev_measure: Measure | None, sink: MutationSink = DIRECT_SINK) -> None:
        sink.set_field(self, "_prev_measure", prev_measure)

    def precedes(self, other: Measure) -> bool:
        next_measure: Measure | None = self._next_measure
        while next_measure is not None:
            if next_measure is other:
                return True

            next_measure = next_measure.next_measure

        return False

    def add_anchor(
        self,
        *,
        anchor: TemporalAnchor,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if anchor.measure is not self:
            raise ValueError("Cannot add anchor that is not in this measure.")

        if anchor.position.value >= self.time_signature.fraction:
            raise ValueError(
                f"Anchor position {anchor.position} lies at or beyond the end of "
                f"the measure (length {self.time_signature.fraction})."
            )

        if anchor in self._anchors:
            return

        if any(anchor.position == a.position for a in self._anchors):
            raise ValueError(f"Anchor with position {anchor.position} already exists.")

        # ordered insertion
        index: int = sum(1 for existing in self._anchors if existing.precedes(anchor))

        sink.list_insert(self._anchors, index, anchor)

    def remove_anchor(
        self,
        *,
        anchor: TemporalAnchor,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if anchor.measure is not self:
            raise ValueError("Cannot remove anchor that is not in this measure.")

        if anchor not in self._anchors:
            return

        sink.list_remove(self._anchors, anchor)
