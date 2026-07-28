from abc import ABC, abstractmethod

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions import MutationAction


class MutationHandler[A: MutationAction](ABC):
    """Executes one action type.
    Returns an entity if it was produced, or None if it was not.
    """

    @abstractmethod
    def handle(
        self,
        *,
        action: A,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None: ...
