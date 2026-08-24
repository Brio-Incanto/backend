from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.base import ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.context.point.voices import VoicesPointContext
    from piano_app.domain.score.document.models.context.span.voices import VoicesSpanContext
    from piano_app.domain.score.document.models.structural.rhythm.metric import (
        RhythmicContainer,
    )


@dataclass(slots=True, kw_only=True, eq=False)
class Voice(ScoreEntity):
    # may be empty at any time
    _children: list[RhythmicContainer] = field(default_factory=list)
    # many-to-many with contexts: a context can name several voices, and one voice
    # can be named by several contexts over time
    _contexts: list[VoicesPointContext | VoicesSpanContext] = field(default_factory=list)

    # no constraint on emptiness in voice
    @property
    def children(self) -> Sequence[RhythmicContainer]:
        return self._children

    @property
    def contexts(self) -> Sequence[VoicesPointContext | VoicesSpanContext]:
        return self._contexts

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

    def add_context(
        self,
        *,
        context: VoicesPointContext | VoicesSpanContext,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in context.voices:
            raise ValueError("Cannot add context that does not name this voice.")

        if context in self._contexts:
            return

        sink.list_append(self._contexts, context)

    def remove_context(
        self,
        *,
        context: VoicesPointContext | VoicesSpanContext,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in context.voices:
            raise ValueError("Cannot remove context that does not name this voice.")

        if context not in self._contexts:
            return

        sink.list_remove(self._contexts, context)
