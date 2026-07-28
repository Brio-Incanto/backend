from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.instructions.actions.material.rest_carrier import (
    CreateRestCarrierAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class CreateRestCarrierHandler:
    """Creates a rest carrier on its owner (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateRestCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        owner: CarrierOwner = resolve(action.owner)
        carrier: RestCarrier = RestCarrier.create(owner=owner, sink=sink)
        return carrier
