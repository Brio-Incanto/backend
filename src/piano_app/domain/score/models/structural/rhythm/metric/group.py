from collections.abc import Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import RhythmicSize

from .base import RhythmicContainer
from .parent import RhythmicContainerParent

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural import TemporalAnchor


@dataclass(slots=True, kw_only=True, eq=False)
class GroupRhythmicContainer(RhythmicContainer):
    # empty allowed only during construction
    _children: list[RhythmicContainer] = field(default_factory=list)

    @property
    def children(self) -> Sequence[RhythmicContainer]:
        return self._children

    @property
    def start_anchor(self) -> TemporalAnchor:
        """The first child's start is the group's start because children are sorted."""
        # use property because it will raise before accessing if no children
        return self.children[0].start_anchor

    @classmethod
    def create(
        cls,
        *,
        parent: RhythmicContainerParent,
        written_size: RhythmicSize,
        occupied_size: RhythmicSize,
        sink: MutationSink = DIRECT_SINK,
    ) -> GroupRhythmicContainer:
        group: GroupRhythmicContainer = cls(
            written_size=written_size,
            occupied_size=occupied_size,
            _parent=parent,
        )

        group.attach(sink=sink)
        return group

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        parent: RhythmicContainerParent,
        written_size: RhythmicSize,
        occupied_size: RhythmicSize,
        sink: MutationSink = DIRECT_SINK,
    ) -> GroupRhythmicContainer:
        group: GroupRhythmicContainer = cls(
            id=id,
            written_size=written_size,
            occupied_size=occupied_size,
            _parent=parent,
        )

        group.attach(sink=sink)
        return group

    def add_child(
        self,
        *,
        child: RhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if child.parent is not self:
            raise ValueError("Cannot add child that belongs to another group.")

        if child in self._children:
            return

        occupied_children_size: Fraction = (
            sum(
                (existing_child.occupied_size.fraction for existing_child in self._children),
                Fraction(0, 1),
            )
            + child.occupied_size.fraction
        )

        if occupied_children_size > self.written_size.fraction:
            raise ValueError(
                "GroupRhythmicContainer cannot contain children whose occupied "
                "size exceeds its written size."
            )

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
            raise ValueError("Cannot remove child that does not belong to this group.")

        if child not in self._children:
            return

        sink.list_remove(self._children, child)
