from piano_app.domain.score.document.models.material import NoteCarrier, RestCarrier
from piano_app.domain.score.document.models.notation import RhythmicSize
from piano_app.domain.score.document.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.document.services.helpers import find_leaf_at
from piano_app.domain.score.document.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateNoteCarrierAction,
    DeleteNoteCarrierAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.material import (
    CreateNoteCarrierRequest,
    DeleteNoteCarrierRequest,
    DeleteNoteRequest,
    DeleteRestCarrierRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.relations import (
    DeleteRelationRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    CreateLeafRequest,
)


class CreateNoteCarrierAnalyzer(MutationAnalyzer[CreateNoteCarrierRequest]):
    """Decides the metric owner of a new note carrier.

    A same-size leaf is reused after deleting its current carrier; otherwise
    creation of a new leaf is delegated.
    """

    def analyze(
        self,
        *,
        request: CreateNoteCarrierRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        leaf: LeafRhythmicContainer | None = find_leaf_at(
            measure=request.measure,
            position=request.position,
            voice=request.voice,
        )

        # if a same-size leaf already exists replace its carrier on it;
        # otherwise a new leaf is created to host the carrier
        owner: Bound[LeafRhythmicContainer]
        if (
            leaf is not None
            and leaf.written_size.value == request.written_value
            and leaf.written_size.count == 1
        ):
            # if something is already attached to the leaf, delete it
            if isinstance(leaf.carrier, NoteCarrier):  # this is unreachable at this point
                buffer.incorporate(item=DeleteNoteCarrierRequest(target=leaf.carrier))
            elif isinstance(leaf.carrier, RestCarrier):
                buffer.incorporate(item=DeleteRestCarrierRequest(target=leaf.carrier))

            owner = leaf
        else:
            owner = ResultRef[LeafRhythmicContainer]()
            buffer.incorporate(
                item=CreateLeafRequest(
                    voice=request.voice,
                    measure=request.measure,
                    position=request.position,
                    size=RhythmicSize(value=request.written_value, count=1),
                    out=owner,
                ),
            )

        buffer.incorporate(
            item=CreateNoteCarrierAction(
                owner=owner,
                articulation=request.articulation,
                out=request.out,
            ),
        )

        return buffer


class DeleteNoteCarrierAnalyzer(MutationAnalyzer[DeleteNoteCarrierRequest]):
    """Decides the note carrier's deletion cascade.

    A group relation is deleted only when it cannot remain valid without this
    carrier; surviving groups lose the carrier during its detach. All notes are
    deleted before the carrier. Cleanup of its owner is deferred to the boundary.
    """

    def analyze(
        self,
        *,
        request: DeleteNoteCarrierRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        note_carrier: NoteCarrier = request.target

        for note_carrier_relation in note_carrier.note_carrier_group_relations:
            if not note_carrier_relation.can_remove_note_carrier(note_carrier=note_carrier):
                buffer.incorporate(item=DeleteRelationRequest(target=note_carrier_relation))

        for carrier_relation in note_carrier.carrier_group_relations:
            if not carrier_relation.can_remove_carrier(carrier=note_carrier):
                buffer.incorporate(item=DeleteRelationRequest(target=carrier_relation))

        for note in note_carrier.notes:
            buffer.incorporate(item=DeleteNoteRequest(target=note))

        buffer.incorporate(item=DeleteNoteCarrierAction(target=request.target))

        return buffer
