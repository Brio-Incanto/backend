from piano_app.domain.score.document.models.material import CarrierOwner, RestCarrier
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.document.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateRestCarrierAction,
    DeleteRestCarrierAction,
)


class CreateRestCarrierHandler(MutationHandler[CreateRestCarrierAction]):
    """Creates a rest carrier on its owner (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateRestCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> RestCarrier:
        owner: CarrierOwner = resolve(action.owner)
        carrier: RestCarrier = RestCarrier.create(
            owner=owner,
            sink=sink,
        )
        return carrier


class DeleteRestCarrierHandler(MutationHandler[DeleteRestCarrierAction]):
    """Detaches a rest carrier from its owner."""

    def handle(
        self,
        *,
        action: DeleteRestCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        rest_carrier: RestCarrier = action.target
        rest_carrier.detach(sink=sink)
        return None
