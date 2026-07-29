from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import RhythmicSize

from .base import RhythmicContainer
from .parent import RhythmicContainerParent

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier import Carrier
    from piano_app.domain.score.models.structural import TemporalAnchor
    from piano_app.domain.score.models.structural.rhythm.grace import GraceGroup


@dataclass(slots=True, kw_only=True, eq=False)
class LeafRhythmicContainer(RhythmicContainer):
    _anchor: TemporalAnchor

    _carrier: Carrier | None = None
    _grace_before: GraceGroup | None = None  # True optional
    _grace_after: GraceGroup | None = None  # True optional

    @property
    def anchor(self) -> TemporalAnchor:
        return self._anchor

    @property
    def carrier(self) -> Carrier | None:
        return self._carrier

    @property
    def grace_before(self) -> GraceGroup | None:
        return self._grace_before

    @property
    def grace_after(self) -> GraceGroup | None:
        return self._grace_after

    @property
    def start_anchor(self) -> TemporalAnchor:
        return self._anchor

    @classmethod
    def create(
        cls,
        *,
        parent: RhythmicContainerParent,
        anchor: TemporalAnchor,
        size: RhythmicSize,
        sink: MutationSink = DIRECT_SINK,
    ) -> LeafRhythmicContainer:
        leaf: LeafRhythmicContainer = cls(
            written_size=size,
            occupied_size=size,
            _parent=parent,
            _anchor=anchor,
        )

        leaf.attach(sink=sink)
        return leaf

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        parent: RhythmicContainerParent,
        anchor: TemporalAnchor,
        size: RhythmicSize,
        sink: MutationSink = DIRECT_SINK,
    ) -> LeafRhythmicContainer:
        leaf: LeafRhythmicContainer = cls(
            id=id,
            written_size=size,
            occupied_size=size,
            _parent=parent,
            _anchor=anchor,
        )

        leaf.attach(sink=sink)
        return leaf

    def attach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        super().attach(sink=sink)

        self._anchor.add_leaf_container(leaf_container=self, sink=sink)

    def detach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._anchor.remove_leaf_container(leaf_container=self, sink=sink)

        super().detach(sink=sink)

    def attach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if carrier.owner is not self:
            raise ValueError("Cannot attach carrier that is not owned by this leaf.")

        if self._carrier is carrier:
            return

        if self._carrier is not None:
            raise ValueError("Cannot attach carrier because leaf already has a carrier.")

        sink.set_field(self, "_carrier", carrier)

    def detach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if carrier.owner is not self:
            raise ValueError("Cannot detach carrier that is not owned by this leaf.")

        if self._carrier is None:
            return

        if self._carrier is not carrier:
            raise ValueError("Cannot detach carrier because leaf does not have this carrier.")

        sink.set_field(self, "_carrier", None)

    def attach_grace_group_before(
        self,
        *,
        grace_group: GraceGroup,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_group.leaf is not self:
            raise ValueError("Cannot attach grace group that is not owned by this leaf.")

        if self._grace_before is grace_group:
            return

        if self._grace_before is not None:
            raise ValueError(
                "Cannot attach grace group because leaf already has a grace group before."
            )

        sink.set_field(self, "_grace_before", grace_group)

    def detach_grace_group_before(
        self,
        *,
        grace_group: GraceGroup,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_group.leaf is not self:
            raise ValueError("Cannot detach grace group that is not owned by this leaf.")

        if self._grace_before is None:
            return

        if self._grace_before is not grace_group:
            raise ValueError(
                "Cannot detach grace group because leaf does not have this grace group before."
            )

        sink.set_field(self, "_grace_before", None)

    def attach_grace_group_after(
        self,
        *,
        grace_group: GraceGroup,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_group.leaf is not self:
            raise ValueError("Cannot attach grace group that is not owned by this leaf.")

        if self._grace_after is grace_group:
            return

        if self._grace_after is not None:
            raise ValueError(
                "Cannot attach grace group because leaf already has a grace group after."
            )

        sink.set_field(self, "_grace_after", grace_group)

    def detach_grace_group_after(
        self,
        *,
        grace_group: GraceGroup,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if grace_group.leaf is not self:
            raise ValueError("Cannot detach grace group that is not owned by this leaf.")

        if self._grace_after is None:
            return

        if self._grace_after is not grace_group:
            raise ValueError(
                "Cannot detach grace group because leaf does not have this grace group after."
            )

        sink.set_field(self, "_grace_after", None)
