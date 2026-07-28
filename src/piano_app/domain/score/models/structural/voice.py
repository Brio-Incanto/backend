from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural.rhythm.metric import (
        RhythmicContainer,
    )


@dataclass(slots=True, kw_only=True, eq=False)
class Voice(ScoreEntity):
    # may be empty at any time
    _children: list[RhythmicContainer] = field(default_factory=list)

    # no constraint on emptiness in voice
    @property
    def children(self) -> Sequence[RhythmicContainer]:
        return self._children

    def add_child(
        self,
        *,
        child: RhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if child.parent is not self:
            # or is not top level
            raise ValueError("Cannot add rhythmic container that belongs to another voice.")

        if child in self._children:
            return

        # ordered insertion
        index: int = sum(1 for existing in self._children if existing.precedes(child))

        sink.list_insert(self._children, index, child)

    def remove_child(
        self,
        *,
        child: RhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if child.parent is not self:
            # or is not top level
            raise ValueError("Cannot remove rhythmic container that belongs to another voice.")

        if child not in self._children:
            return

        sink.list_remove(self._children, child)
