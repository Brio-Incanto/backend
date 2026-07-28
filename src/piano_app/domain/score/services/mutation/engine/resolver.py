from typing import Any, cast

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions import Bound, ResultRef


class Resolver:
    """Resolves an action input to a concrete entity at execution time.

    Passes existing entities through unchanged and looks up ``ResultRef``
    placeholders in the run-time environment.
    """

    def __init__(self) -> None:
        self._env: dict[ResultRef[Any], ScoreEntity] = {}

    # T is unbounded, not ``ScoreEntity``: a ref is typed by the capability the
    # consumer wants (``CarrierOwner``, ``RhythmicContainerParent`` — protocols the
    # concrete entity satisfies), while the env stores it as a ``ScoreEntity``.
    def __call__[T](self, value: Bound[T]) -> T:
        if isinstance(value, ResultRef):
            return cast(T, self._env[value])

        return value

    def register(self, ref: ResultRef[Any], entity: ScoreEntity) -> None:
        self._env[ref] = entity
