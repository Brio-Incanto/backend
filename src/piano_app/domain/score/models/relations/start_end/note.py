from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import GlissandoType
from piano_app.domain.shared.abstract import abstract

from .base import StartEndRelation

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.primitive import Note


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class NoteToNoteRelation(StartEndRelation["Note"]):
    start: Note
    end: Note

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.start.add_relation(relation=self, sink=sink)
        self.end.add_relation(relation=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.start.remove_relation(relation=self, sink=sink)
        self.end.remove_relation(relation=self, sink=sink)


@dataclass(slots=True, kw_only=True, eq=False)
class Tie(NoteToNoteRelation):
    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_available_notes()

        # TODO check notes pitch

    @classmethod
    def create(
        cls,
        *,
        start_note: Note,
        end_note: Note,
        sink: MutationSink = DIRECT_SINK,
    ) -> Tie:
        relation: Tie = cls(
            start=start_note,
            end=end_note,
        )

        relation.attach(sink=sink)
        return relation

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start_note: Note,
        end_note: Note,
        sink: MutationSink = DIRECT_SINK,
    ) -> Tie:
        relation: Tie = cls(
            id=id,
            start=start_note,
            end=end_note,
        )

        relation.attach(sink=sink)
        return relation

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._validate_available_notes()
        super().attach(sink=sink)

    def _validate_available_notes(self) -> None:
        if any(
            isinstance(relation, Tie)
            for relation in self.start.relations
            if relation is not self and relation.start is self.start
        ):
            raise ValueError("Note already starts another tie.")

        if any(
            isinstance(relation, Tie)
            for relation in self.end.relations
            if relation is not self and relation.end is self.end
        ):
            raise ValueError("Note already ends another tie.")


@dataclass(slots=True, kw_only=True, eq=False)
class Glissando(NoteToNoteRelation):
    glissando_type: GlissandoType

    @classmethod
    def create(
        cls,
        *,
        start_note: Note,
        end_note: Note,
        glissando_type: GlissandoType,
        sink: MutationSink = DIRECT_SINK,
    ) -> Glissando:
        relation: Glissando = cls(
            start=start_note,
            end=end_note,
            glissando_type=glissando_type,
        )

        relation.attach(sink=sink)
        return relation

    def __post_init__(self) -> None:
        super().__post_init__()

        # TODO check different pitch
