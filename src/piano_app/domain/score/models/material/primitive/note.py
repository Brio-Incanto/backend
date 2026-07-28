from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import Accidental, Fingering

from .base import MusicalItem

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier import NoteCarrier
    from piano_app.domain.score.models.relations.start_end import NoteToNoteRelation
    from piano_app.domain.score.models.structural import Staff


@dataclass(slots=True, kw_only=True, eq=False)
class Note(MusicalItem):
    """A representation of a musical note, only notation, pitch is derived on demand."""

    accidental: Accidental
    fingering: Fingering

    _note_carrier: NoteCarrier
    _relations: list[NoteToNoteRelation] = field(default_factory=list)

    @property
    def note_carrier(self) -> NoteCarrier:
        return self._note_carrier

    @property
    def relations(self) -> Sequence[NoteToNoteRelation]:
        return self._relations

    @classmethod
    def create(
        cls,
        *,
        note_carrier: NoteCarrier,
        staff: Staff,
        staff_step: int,
        accidental: Accidental,
        fingering: Fingering = Fingering.NONE,
        sink: MutationSink = DIRECT_SINK,
    ) -> Note:
        note: Note = cls(
            staff_step=staff_step,
            _staff=staff,
            _note_carrier=note_carrier,
            accidental=accidental,
            fingering=fingering,
        )

        note.attach(sink=sink)
        return note

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        self._note_carrier.add_note(note=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._note_carrier.remove_note(note=self, sink=sink)
        super().detach(sink=sink)

    def add_relation(
        self,
        *,
        relation: NoteToNoteRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if relation.start is not self and relation.end is not self:
            raise ValueError("Relation must be connected to this note.")

        if relation in self._relations:
            return

        sink.list_append(self._relations, relation)

    def remove_relation(
        self,
        *,
        relation: NoteToNoteRelation,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if relation.start is not self and relation.end is not self:
            raise ValueError("Relation must be connected to this note.")

        if relation not in self._relations:
            return

        sink.list_remove(self._relations, relation)
