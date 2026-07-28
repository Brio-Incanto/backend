from collections.abc import Sequence

from piano_app.domain.score.models import ScoreDocument, ScoreEntity
from piano_app.domain.score.models.material import Note, NoteCarrier, Rest, RestCarrier
from piano_app.domain.score.models.notation import (
    Accidental,
    DottedRhythmicValue,
    Fingering,
    RhythmicValue,
)
from piano_app.domain.score.models.relations.start_end import Tie
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    Voice,
)
from piano_app.domain.score.services.mutation.instructions import (
    MutationRejectedError,
    MutationRequest,
    ResultRef,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    CreateNoteRequest,
    DeleteNoteCarrierRequest,
    DeleteNoteRequest,
    DeleteRestCarrierRequest,
    DeleteRestRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations import (
    CreateTieRequest,
)
from piano_app.domain.score.services.resolution import ScoreEntityResolver

from .intents import DeleteBatchIntent, InsertNoteIntent, TieNotesIntent


# TODO split into smaller pieces
class MutationCompiler:
    """Entry / command-compiler: turns a coarse edit intent into the fine
    engine requests the drain unfolds.

    Deterministic — it reads the document grid, mints the SSA ``out`` ref, and never
    mutates. This is the seam where pre-computable decomposition lives.
    """

    # TODO add support of cross measure slicing
    def compile_insert_note(
        self,
        *,
        document: ScoreDocument,
        intent: InsertNoteIntent,
    ) -> Sequence[MutationRequest]:
        entities_by_id: dict[str, ScoreEntity] = self._resolve(
            document=document,
            entity_ids=(intent.voice_id, intent.staff_id, intent.measure_id),
        )
        voice: Voice = self._expect(
            entities_by_id=entities_by_id,
            entity_id=intent.voice_id,
            expected=Voice,
        )
        staff: Staff = self._expect(
            entities_by_id=entities_by_id,
            entity_id=intent.staff_id,
            expected=Staff,
        )
        measure: Measure = self._expect(
            entities_by_id=entities_by_id,
            entity_id=intent.measure_id,
            expected=Measure,
        )
        try:
            position = MeasurePosition.of(
                numerator=intent.position.numerator,
                denominator=intent.position.denominator,
            )
            written_value = DottedRhythmicValue(
                value=RhythmicValue(intent.written_value.value),
                dots_count=intent.written_value.dots,
            )
            accidental = Accidental(intent.accidental)
            fingering = Fingering(intent.fingering)
        except (ValueError, ZeroDivisionError) as error:
            raise MutationRejectedError(f"Invalid insert-note command: {error}") from error

        return [
            CreateNoteRequest(
                voice=voice,
                staff=staff,
                measure=measure,
                position=position,
                written_value=written_value,
                staff_step=intent.staff_step,
                accidental=accidental,
                fingering=fingering,
                out=ResultRef[Note](),
            )
        ]

    def compile_delete_batch(
        self,
        *,
        document: ScoreDocument,
        intent: DeleteBatchIntent,
    ) -> Sequence[MutationRequest]:
        """Compile one mixed delete gesture, pruning children of selected carriers.

        Selection order is retained within each level, while carriers are emitted before
        primitives because their analyzers own the downward cascade. Aggregate and
        relation deletion are not supported by this command yet.
        """
        unique_ids: tuple[str, ...] = tuple(dict.fromkeys(intent.entity_ids))
        if not unique_ids:
            raise MutationRejectedError("Delete batch must contain at least one entity id.")

        entities_by_id: dict[str, ScoreEntity] = self._resolve(
            document=document,
            entity_ids=unique_ids,
        )
        resolved_entities: list[ScoreEntity] = [
            entities_by_id[entity_id] for entity_id in unique_ids
        ]

        unsupported_entities: list[ScoreEntity] = [
            entity
            for entity in resolved_entities
            if not isinstance(entity, Note | NoteCarrier | Rest | RestCarrier)
        ]
        if unsupported_entities:
            targets_description: str = ", ".join(
                f"{type(entity).__name__}({entity.id!r})" for entity in unsupported_entities
            )
            raise MutationRejectedError(f"Unsupported delete targets: {targets_description}.")

        note_carriers: list[NoteCarrier] = [
            entity for entity in resolved_entities if isinstance(entity, NoteCarrier)
        ]
        rest_carriers: list[RestCarrier] = [
            entity for entity in resolved_entities if isinstance(entity, RestCarrier)
        ]
        notes: list[Note] = [
            entity
            for entity in resolved_entities
            if isinstance(entity, Note) and entity.note_carrier not in note_carriers
        ]
        rests: list[Rest] = [
            entity
            for entity in resolved_entities
            if isinstance(entity, Rest) and entity.rest_carrier not in rest_carriers
        ]

        return [
            *(DeleteNoteCarrierRequest(target=carrier) for carrier in note_carriers),
            *(DeleteRestCarrierRequest(target=carrier) for carrier in rest_carriers),
            *(DeleteNoteRequest(target=note) for note in notes),
            *(DeleteRestRequest(target=rest) for rest in rests),
        ]

    def compile_tie_notes(
        self,
        *,
        document: ScoreDocument,
        intent: TieNotesIntent,
    ) -> Sequence[MutationRequest]:
        entities_by_id: dict[str, ScoreEntity] = self._resolve(
            document=document,
            entity_ids=(intent.start_note_id, intent.end_note_id),
        )
        start_note: Note = self._expect(
            entities_by_id=entities_by_id,
            entity_id=intent.start_note_id,
            expected=Note,
        )
        end_note: Note = self._expect(
            entities_by_id=entities_by_id,
            entity_id=intent.end_note_id,
            expected=Note,
        )

        return [CreateTieRequest(start_note=start_note, end_note=end_note, out=ResultRef[Tie]())]

    @staticmethod
    def _resolve(
        *,
        document: ScoreDocument,
        entity_ids: Sequence[str],
    ) -> dict[str, ScoreEntity]:
        try:
            return ScoreEntityResolver(document=document).resolve(ids=set(entity_ids))
        except ValueError as error:
            raise MutationRejectedError(str(error)) from error

    @staticmethod
    def _expect[E: ScoreEntity](
        *,
        entities_by_id: dict[str, ScoreEntity],
        entity_id: str,
        expected: type[E],
    ) -> E:
        entity: ScoreEntity | None = entities_by_id.get(entity_id)
        if not isinstance(entity, expected):
            raise MutationRejectedError(
                f"Entity {entity_id!r} must be {expected.__name__}, "
                f"got {type(entity).__name__ if entity is not None else 'nothing'}."
            )

        return entity
