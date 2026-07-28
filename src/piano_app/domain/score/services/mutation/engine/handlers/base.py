from typing import Protocol

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.instructions import MutationAction
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class MutationHandler[A: MutationAction](Protocol):
    """Executes one action type.
    Returns an entity if it was produced, or None if it was not.
    """

    def handle(
        self,
        *,
        action: A,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None: ...
