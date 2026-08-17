from piano_app.domain.score.document.models.material import Rest, RestCarrier
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateRestAction,
    DeleteRestAction,
)


class CreateRestHandler:
    """Creates a rest inside its carrier (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateRestAction,
        resolve: ResolveBound,
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


class DeleteRestHandler:
    """Detaches a rest from its carrier."""

    def handle(
        self,
        *,
        action: DeleteRestAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        rest: Rest = action.target
        rest.detach(sink=sink)
        return None
