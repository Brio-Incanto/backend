from piano_app.domain.score.document.models.material import CarrierOwner, RestCarrier
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateRestCarrierAction,
    DeleteRestCarrierAction,
)


class CreateRestCarrierHandler:
    """Creates a rest carrier on its owner (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateRestCarrierAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> RestCarrier:
        owner: CarrierOwner = resolve(action.owner)
        carrier: RestCarrier = RestCarrier.create(
            owner=owner,
            sink=sink,
        )
        return carrier


class DeleteRestCarrierHandler:
    """Detaches a rest carrier from its owner."""

    def handle(
        self,
        *,
        action: DeleteRestCarrierAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        rest_carrier: RestCarrier = action.target
        rest_carrier.detach(sink=sink)
        return None
