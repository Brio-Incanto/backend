from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import DottedRhythmicValue

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier import Carrier

    from .group import GraceGroup


@dataclass(slots=True, kw_only=True, eq=False)
class GraceItem(ScoreEntity):
    rhythmic_value: DottedRhythmicValue

    _grace_group: GraceGroup
    _carrier: Carrier | None = None

    @property
    def grace_group(self) -> GraceGroup:
        return self._grace_group

    @property
    def carrier(self) -> Carrier | None:
        return self._carrier

    @classmethod
    def create(
        cls,
        *,
        grace_group: GraceGroup,
        rhythmic_value: DottedRhythmicValue,
        sink: MutationSink = DIRECT_SINK,
    ) -> GraceItem:
        grace_item: GraceItem = cls(
            rhythmic_value=rhythmic_value,
            _grace_group=grace_group,
        )

        grace_item.attach(sink=sink)
        return grace_item

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        grace_group: GraceGroup,
        rhythmic_value: DottedRhythmicValue,
        sink: MutationSink = DIRECT_SINK,
    ) -> GraceItem:
        grace_item: GraceItem = cls(
            id=id,
            rhythmic_value=rhythmic_value,
            _grace_group=grace_group,
        )

        grace_item.attach(sink=sink)
        return grace_item

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._grace_group.add_grace_item(grace_item=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._grace_group.remove_grace_item(grace_item=self, sink=sink)

    def attach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if carrier.owner is not self:
            raise ValueError("Cannot attach carrier that is not owned by this grace item.")

        if self._carrier is carrier:
            return

        if self._carrier is not None:
            raise ValueError("Cannot attach carrier because grace item already has a carrier.")

        sink.set_field(self, "_carrier", carrier)

    def detach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if carrier.owner is not self:
            raise ValueError("Cannot detach carrier that is not owned by this grace item.")

        if self._carrier is None:
            return

        if self._carrier is not carrier:
            raise ValueError("Cannot detach carrier because grace item does not have this carrier.")

        sink.set_field(self, "_carrier", None)
