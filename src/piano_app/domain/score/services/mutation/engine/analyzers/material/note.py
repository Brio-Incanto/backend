from piano_app.domain.score.models.material import Carrier
from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import find_leaf_at
from piano_app.domain.score.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material import (
    CreateNoteAction,
    DeleteNoteAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    CreateNoteCarrierRequest,
    CreateNoteRequest,
    DeleteNoteRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations import (
    DeleteRelationRequest,
)


class CreateNoteAnalyzer(MutationAnalyzer[CreateNoteRequest]):
    """Decides where to create a note in the requested voice slot.

    A same-size leaf with a note carrier triggers a chord join; every other slot
    state delegates creation of a suitable carrier.
    """

    def analyze(self, *, request: CreateNoteRequest, resolver: ResolveBound) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        leaf: LeafRhythmicContainer | None = find_leaf_at(
            measure=request.measure,
            position=request.position,
            voice=request.voice,
        )
        carrier: Carrier | None = leaf.carrier if leaf is not None else None

        # chord-join only when the slot already holds a same-size note carrier;
        # everything else (rest carrier, different size, no leaf) is the carrier's call
        note_carrier: Bound[NoteCarrier]
        if (
            leaf is not None
            and leaf.written_size.value == request.written_value
            and leaf.written_size.count == 1
            and isinstance(carrier, NoteCarrier)
        ):
            # TODO:
            #   PITCH-VALIDATION (deferred — pitch is not in v1): when the carrier already
            #   holds a note at the SAME pitch, chord-duplicate is forbidden → reject (or
            #   replace); cross-voice unison stays allowed. See [[pitch-and-voice-policy]].
            #   No-op until pitch lands.
            note_carrier = carrier
        else:
            note_carrier = ResultRef[NoteCarrier]()
            buffer.incorporate(
                item=CreateNoteCarrierRequest(
                    voice=request.voice,
                    measure=request.measure,
                    position=request.position,
                    written_value=request.written_value,
                    out=note_carrier,
                ),
            )

        buffer.incorporate(
            item=CreateNoteAction(
                note_carrier=note_carrier,
                staff=request.staff,
                staff_step=request.staff_step,
                accidental=request.accidental,
                fingering=request.fingering,
                out=request.out,
            ),
        )

        return buffer


class DeleteNoteAnalyzer(MutationAnalyzer[DeleteNoteRequest]):
    """Decides the note's deletion cascade.

    Note-to-note relations are deleted before the note. Cleanup of an empty
    carrier is deferred to the mutation boundary.
    """

    def analyze(self, *, request: DeleteNoteRequest, resolver: ResolveBound) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        note: Note = request.target

        for note_relation in note.relations:
            buffer.incorporate(item=DeleteRelationRequest(target=note_relation))

        buffer.incorporate(item=DeleteNoteAction(target=note))

        return buffer
