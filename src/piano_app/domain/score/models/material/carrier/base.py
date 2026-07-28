from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
    from piano_app.domain.score.models.relations.group import CarrierGroupRelation


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class Carrier(ScoreEntity):
    _owner: CarrierOwner

    _carrier_group_relations: list[CarrierGroupRelation] = field(default_factory=list)

    @property
    def owner(self) -> CarrierOwner:
        return self._owner

    @property
    def carrier_group_relations(self) -> Sequence[CarrierGroupRelation]:
        return self._carrier_group_relations

    def attach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._owner.attach_carrier(carrier=self, sink=sink)

    def detach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if any(
            not relation.can_remove_carrier(carrier=self)
            for relation in self._carrier_group_relations
        ):
            raise ValueError("Cannot detach carrier without invalidating a group relation.")

        while self._carrier_group_relations:
            self._carrier_group_relations[0].remove_carrier(carrier=self, sink=sink)

        self._owner.detach_carrier(carrier=self, sink=sink)

    def add_carrier_group_relation(
        self,
        *,
        relation: CarrierGroupRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in relation.members:
            raise ValueError("Carrier is not part of this group relation.")

        if relation in self._carrier_group_relations:
            return

        sink.list_append(self._carrier_group_relations, relation)

    def remove_carrier_group_relation(
        self,
        *,
        relation: CarrierGroupRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in relation.members:
            raise ValueError("Carrier is not part of this group relation.")

        if relation not in self._carrier_group_relations:
            return

        sink.list_remove(self._carrier_group_relations, relation)
