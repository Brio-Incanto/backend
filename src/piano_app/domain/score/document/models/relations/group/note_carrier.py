from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import ArpeggioType
from piano_app.domain.shared.abstract import abstract

from .base import GroupRelation

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.material.carrier import NoteCarrier


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class NoteCarrierGroupRelation(GroupRelation["NoteCarrier"]):
    _members: list[NoteCarrier]

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        for note_carrier in self._members:
            note_carrier.add_note_carrier_group_relation(relation=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        for note_carrier in self._members:
            note_carrier.remove_note_carrier_group_relation(relation=self, sink=sink)

    def remove_note_carrier(
        self,
        *,
        note_carrier: NoteCarrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if note_carrier not in self._members:
            if self in note_carrier.note_carrier_group_relations:
                raise ValueError(
                    "Note-carrier group relation references a non-member note carrier."
                )

            return

        if self not in note_carrier.note_carrier_group_relations:
            raise ValueError("Note-carrier group relation is missing from the note carrier.")

        if not self.can_remove_note_carrier(note_carrier=note_carrier):
            raise ValueError("Cannot remove note carrier without invalidating its group relation.")

        note_carrier.remove_note_carrier_group_relation(relation=self, sink=sink)
        sink.list_remove(self._members, note_carrier)

    def can_remove_note_carrier(self, *, note_carrier: NoteCarrier) -> bool:
        if note_carrier not in self._members:
            raise ValueError("Note carrier is not a member of this group relation.")

        return len(self._members) > 1


# TODO Arpeggio is not supported yet. Revisit its membership before implementation:
# the relation semantically connects notes, not their carriers.
@dataclass(slots=True, kw_only=True, eq=False)
class Arpeggio(NoteCarrierGroupRelation):
    arpeggio_type: ArpeggioType = ArpeggioType.ARPEGGIATO

    def __post_init__(self) -> None:
        super().__post_init__()

        note_count: int = sum(len(carrier.notes) for carrier in self._members)
        if note_count < 2:
            raise ValueError("Arpeggio must contain at least two notes.")

        for note_carrier in self._members:
            self._validate_available_note_carrier(note_carrier=note_carrier)

    @classmethod
    def create(
        cls,
        *,
        note_carriers: list[NoteCarrier],
        arpeggio_type: ArpeggioType = ArpeggioType.ARPEGGIATO,
        sink: MutationSink = DIRECT_SINK,
    ) -> Arpeggio:
        arpeggio: Arpeggio = cls(
            _members=list(note_carriers),
            arpeggio_type=arpeggio_type,
        )
        arpeggio.attach(sink=sink)
        return arpeggio

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        for note_carrier in self._members:
            self._validate_available_note_carrier(note_carrier=note_carrier)

        super().attach(sink=sink)

    def can_remove_note_carrier(self, *, note_carrier: NoteCarrier) -> bool:
        if note_carrier not in self._members:
            raise ValueError("Note carrier is not a member of this arpeggio.")

        remaining_note_count: int = sum(
            len(member.notes) for member in self._members if member is not note_carrier
        )
        return remaining_note_count >= 2

    def _validate_available_note_carrier(self, *, note_carrier: NoteCarrier) -> None:
        if any(
            isinstance(group_relation, Arpeggio)
            for group_relation in note_carrier.note_carrier_group_relations
            if group_relation is not self
        ):
            raise ValueError("Note carrier is already part of another arpeggio.")
