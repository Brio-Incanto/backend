from typing import Any, Protocol, cast

from piano_app.domain.score.document.models import ScoreEntity
from piano_app.domain.score.document.services.mutation.instructions import Bound, ResultRef


class ResolveBound(Protocol):
    """A protocol for a function that resolves a work-item input to a concrete entity
    without an ability to register anything.
    """

    def __call__[T](self, value: Bound[T]) -> T: ...


class Resolver:
    """Resolves a work-item input to a concrete entity at execution time.

    Passes existing entities through unchanged and looks up ``ResultRef``
    placeholders in the run-time environment.
    """

    def __init__(self) -> None:
        self._bindings: dict[ResultRef[Any], ScoreEntity] = {}

    # T is unbounded, not ``ScoreEntity`` to avoid static analyzer complaints
    # Being a subclass of ''ScoreEntity'' is guaranteed by using ''register'' method
    def __call__[T](self, value: Bound[T]) -> T:
        if isinstance(value, ResultRef):
            return cast(T, self._bindings[value])

        return value

    def register(
        self,
        *,
        reference: ResultRef[Any],
        entity: ScoreEntity,
    ) -> None:
        if reference in self._bindings:
            raise ValueError("ResultRef already has a producer in this gesture.")

        self._bindings[reference] = entity
