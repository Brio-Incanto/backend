from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.material.primitive import Rest
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.material.rest import (
    CreateRestAction,
    DeleteRestAction,
)


class CreateRestHandler(MutationHandler[CreateRestAction]):
    """Creates a rest inside its carrier (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateRestAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> Rest:
        rest_carrier: RestCarrier = resolve(action.rest_carrier)
        rest: Rest = Rest.create(
            rest_carrier=rest_carrier,
            staff=action.staff,
            staff_step=action.staff_step,
            sink=sink,
        )
        return rest


class DeleteRestHandler(MutationHandler[DeleteRestAction]):
    """Detaches a rest from its carrier."""

    def handle(
        self,
        *,
        action: DeleteRestAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        rest: Rest = action.target
        rest.detach(sink=sink)
        return None
