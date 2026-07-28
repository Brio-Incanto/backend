from piano_app.domain.score.models.material import Carrier, Rest, RestCarrier
from piano_app.domain.score.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import find_leaf_at
from piano_app.domain.score.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material import (
    CreateRestAction,
    DeleteRestAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    CreateRestCarrierRequest,
    CreateRestRequest,
    DeleteRestRequest,
)


class CreateRestAnalyzer(MutationAnalyzer[CreateRestRequest]):
    """Decides where to create a rest in the requested voice slot.

    A same-size leaf with a rest carrier triggers replacement of its rest; every
    other slot state delegates creation of a suitable carrier.
    """

    def analyze(
        self,
        *,
        request: CreateRestRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        leaf: LeafRhythmicContainer | None = find_leaf_at(
            measure=request.measure,
            position=request.position,
            voice=request.voice,
        )
        carrier: Carrier | None = leaf.carrier if leaf is not None else None

        rest_carrier: Bound[RestCarrier]
        if (
            leaf is not None
            and leaf.written_size.value == request.written_value
            and leaf.written_size.count == 1
            and isinstance(carrier, RestCarrier)
        ):
            # replace the existing rest on the carrier
            rest: Rest | None = carrier.rest
            if rest is not None:
                buffer.incorporate(item=DeleteRestRequest(target=rest))

            rest_carrier = carrier
        else:
            rest_carrier = ResultRef[RestCarrier]()
            buffer.incorporate(
                item=CreateRestCarrierRequest(
                    voice=request.voice,
                    measure=request.measure,
                    position=request.position,
                    written_value=request.written_value,
                    out=rest_carrier,
                ),
            )

        buffer.incorporate(
            item=CreateRestAction(
                rest_carrier=rest_carrier,
                staff=request.staff,
                staff_step=request.staff_step,
                out=request.out,
            ),
        )

        return buffer


class DeleteRestAnalyzer(MutationAnalyzer[DeleteRestRequest]):
    """Decides direct deletion of a rest because it owns no child entities."""

    def analyze(
        self,
        *,
        request: DeleteRestRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        rest: Rest = request.target

        buffer.incorporate(item=DeleteRestAction(target=rest))

        return buffer
