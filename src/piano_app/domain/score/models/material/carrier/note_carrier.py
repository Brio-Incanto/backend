from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import Articulation

from .base import Carrier

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
    from piano_app.domain.score.models.material.primitive.note import Note
    from piano_app.domain.score.models.relations.group import NoteCarrierGroupRelation


# TODO validate note addition by absolute pitch. Pitch may be a key for dict
@dataclass(slots=True, kw_only=True, eq=False)
class NoteCarrier(Carrier):
    articulation: Articulation = Articulation.NONE

    _notes: list[Note] = field(default_factory=list)
    _note_carrier_group_relations: list[NoteCarrierGroupRelation] = field(default_factory=list)

    @property
    def notes(self) -> Sequence[Note]:
        return self._notes

    @property
    def note_carrier_group_relations(self) -> Sequence[NoteCarrierGroupRelation]:
        return self._note_carrier_group_relations

    @classmethod
    def create(
        cls,
        *,
        owner: CarrierOwner,
        articulation: Articulation = Articulation.NONE,
        sink: MutationSink = DIRECT_SINK,
    ) -> NoteCarrier:
        carrier: NoteCarrier = cls(
            _owner=owner,
            articulation=articulation,
        )

        carrier.attach(sink=sink)
        return carrier

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        owner: CarrierOwner,
        articulation: Articulation = Articulation.NONE,
        sink: MutationSink = DIRECT_SINK,
    ) -> NoteCarrier:
        carrier: NoteCarrier = cls(
            id=id,
            _owner=owner,
            articulation=articulation,
        )

        carrier.attach(sink=sink)
        return carrier

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        if any(
            not relation.can_remove_note_carrier(note_carrier=self)
            for relation in self._note_carrier_group_relations
        ):
            raise ValueError("Cannot detach note carrier without invalidating a group relation.")

        if any(
            not relation.can_remove_carrier(carrier=self)
            for relation in self._carrier_group_relations
        ):
            raise ValueError("Cannot detach note carrier without invalidating a group relation.")

        while self._note_carrier_group_relations:
            self._note_carrier_group_relations[0].remove_note_carrier(
                note_carrier=self,
                sink=sink,
            )

        super().detach(sink=sink)

    def add_note(
        self,
        *,
        note: Note,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if note.note_carrier is not self:
            raise ValueError("Cannot add note that belongs to another note carrier.")

        if note in self._notes:
            return

        sink.list_append(self._notes, note)

    def remove_note(
        self,
        *,
        note: Note,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if note.note_carrier is not self:
            raise ValueError("Cannot remove note that is not in this note carrier.")

        if note not in self._notes:
            return

        if note.relations:
            raise ValueError("Cannot remove note while it belongs to a relation.")

        sink.list_remove(self._notes, note)

    def add_note_carrier_group_relation(
        self,
        *,
        relation: NoteCarrierGroupRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in relation.members:
            raise ValueError("Note carrier is not part of this group relation.")

        if relation in self._note_carrier_group_relations:
            return

        sink.list_append(self._note_carrier_group_relations, relation)

    def remove_note_carrier_group_relation(
        self,
        *,
        relation: NoteCarrierGroupRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if self not in relation.members:
            raise ValueError("Note carrier is not part of this group relation.")

        if relation not in self._note_carrier_group_relations:
            return

        sink.list_remove(self._note_carrier_group_relations, relation)
