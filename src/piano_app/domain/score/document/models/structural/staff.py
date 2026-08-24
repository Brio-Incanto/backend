from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.base import ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.context.point.staff import StaffPointContext
    from piano_app.domain.score.document.models.context.span.staff import StaffSpanContext
    from piano_app.domain.score.document.models.material.primitive import MusicalItem


@dataclass(slots=True, kw_only=True, eq=False)
class Staff(ScoreEntity):
    _musical_items: list[MusicalItem] = field(default_factory=list)
    _contexts: list[StaffPointContext | StaffSpanContext] = field(default_factory=list)

    @property
    def musical_items(self) -> Sequence[MusicalItem]:
        return self._musical_items

    @property
    def contexts(self) -> Sequence[StaffPointContext | StaffSpanContext]:
        return self._contexts

    def add_musical_item(
        self,
        *,
        musical_item: MusicalItem,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if musical_item.staff is not self:
            raise ValueError("Cannot add musical item that belongs to another staff.")

        if musical_item in self._musical_items:
            return

        sink.list_append(self._musical_items, musical_item)

    def remove_musical_item(
        self,
        *,
        musical_item: MusicalItem,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if musical_item.staff is not self:
            raise ValueError("Cannot remove musical item that is not in this staff.")

        if musical_item not in self._musical_items:
            return

        sink.list_remove(self._musical_items, musical_item)

    def add_context(
        self,
        *,
        context: StaffPointContext | StaffSpanContext,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if context.staff is not self:
            raise ValueError("Cannot add context that is scoped to another staff.")

        if context in self._contexts:
            return

        sink.list_append(self._contexts, context)

    def remove_context(
        self,
        *,
        context: StaffPointContext | StaffSpanContext,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if context.staff is not self:
            raise ValueError("Cannot remove context that is not scoped to this staff.")

        if context not in self._contexts:
            return

        sink.list_remove(self._contexts, context)
