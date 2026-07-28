from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import GracePlacement, GraceType

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural.rhythm.metric import (
        LeafRhythmicContainer,
    )

    from .item import GraceItem


@dataclass(slots=True, kw_only=True, eq=False)
class GraceGroup(ScoreEntity):
    grace_type: GraceType
    placement: GracePlacement
    _leaf: LeafRhythmicContainer

    # empty allowed only during construction
    _grace_items: list[GraceItem] = field(default_factory=list)

    @property
    def leaf(self) -> LeafRhythmicContainer:
        return self._leaf

    # enforce at least one grace item in the group
    @property
    def grace_items(self) -> Sequence[GraceItem]:
        return self._grace_items

    @classmethod
    def create(
        cls,
        *,
        leaf: LeafRhythmicContainer,
        grace_type: GraceType,
        placement: GracePlacement,
        sink: MutationSink = DIRECT_SINK,
    ) -> GraceGroup:
        group: GraceGroup = cls(
            grace_type=grace_type,
            placement=placement,
            _leaf=leaf,
        )

        group.attach(sink=sink)
        return group

    def attach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self.placement is GracePlacement.BEFORE:
            self._leaf.attach_grace_group_before(grace_group=self, sink=sink)
        else:
            self._leaf.attach_grace_group_after(grace_group=self, sink=sink)

    def detach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self.placement is GracePlacement.BEFORE:
            self._leaf.detach_grace_group_before(grace_group=self, sink=sink)
        else:
            self._leaf.detach_grace_group_after(grace_group=self, sink=sink)

    def add_grace_item(
        self,
        *,
        grace_item: GraceItem,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_item.grace_group is not self:
            raise ValueError("Cannot add grace item that belongs to another group.")

        if grace_item in self._grace_items:
            return

        sink.list_append(self._grace_items, grace_item)

    def remove_grace_item(
        self,
        *,
        grace_item: GraceItem,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_item.grace_group is not self:
            raise ValueError("Cannot remove grace item that belongs to another group.")

        if grace_item not in self._grace_items:
            return

        sink.list_remove(self._grace_items, grace_item)
