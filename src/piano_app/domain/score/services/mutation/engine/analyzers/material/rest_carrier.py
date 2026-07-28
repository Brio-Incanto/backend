from piano_app.domain.score.models.material import NoteCarrier, Rest, RestCarrier
from piano_app.domain.score.models.notation import RhythmicSize
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import find_leaf_at
from piano_app.domain.score.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material.rest_carrier import (
    CreateRestCarrierAction,
    DeleteRestCarrierAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    DeleteNoteCarrierRequest,
    DeleteRestRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.material.rest_carrier import (
    CreateRestCarrierRequest,
    DeleteRestCarrierRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations import (
    DeleteRelationRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.rhythmic.leaf import (
    CreateLeafRequest,
)


class CreateRestCarrierAnalyzer(MutationAnalyzer[CreateRestCarrierRequest]):
    """Decides the metric owner of a new rest carrier.

    A same-size leaf is reused after deleting its current carrier; otherwise
    creation of a new leaf is delegated.
    """

    def analyze(
        self,
        *,
        request: CreateRestCarrierRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        leaf: LeafRhythmicContainer | None = find_leaf_at(
            measure=request.measure,
            position=request.position,
            voice=request.voice,
        )

        owner: Bound[LeafRhythmicContainer]
        if (
            leaf is not None
            and leaf.written_size.value == request.written_value
            and leaf.written_size.count == 1
        ):
            # if something is already attached to the leaf, delete it
            if isinstance(leaf.carrier, NoteCarrier):
                buffer.incorporate(item=DeleteNoteCarrierRequest(target=leaf.carrier))
            elif isinstance(leaf.carrier, RestCarrier):  # this is unreachable at this point
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
            item=CreateRestCarrierAction(
                owner=owner,
                out=request.out,
            )
        )

        return buffer


class DeleteRestCarrierAnalyzer(MutationAnalyzer[DeleteRestCarrierRequest]):
    """Decides the rest carrier's deletion cascade.

    A group relation is deleted only when it cannot remain valid without this
    carrier; surviving groups lose the carrier during its detach. The optional
    rest is deleted before the carrier. Owner cleanup is deferred to the boundary.
    """

    def analyze(
        self,
        *,
        request: DeleteRestCarrierRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        rest_carrier: RestCarrier = request.target

        for relation in rest_carrier.carrier_group_relations:
            if not relation.can_remove_carrier(carrier=rest_carrier):
                buffer.incorporate(item=DeleteRelationRequest(target=relation))

        rest: Rest | None = rest_carrier.rest
        if rest is not None:
            buffer.incorporate(item=DeleteRestRequest(target=rest))

        buffer.incorporate(item=DeleteRestCarrierAction(target=rest_carrier))

        return buffer
