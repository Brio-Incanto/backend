from collections.abc import Sequence

from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
    MutationAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
    MutationRequest,
)

from .typing import MutationWorkItem


class EmitBuffer:
    """Collects the work items one analyzer emits while expanding a request.

    Guards that the only action an analyzer may emit is **its request's own terminal**,
    one whose produced entity matches the request (create by ``out``, delete by ``target``).
    Everything else must be a request (a delegated dependency or a cascade).
    """

    def __init__(self, *, request: MutationRequest) -> None:
        self._request: MutationRequest = request
        self._items: list[MutationWorkItem] = []
        self._action_emitted: bool = False

    @property
    def items(self) -> Sequence[MutationWorkItem]:
        return self._items

    def incorporate(self, *, item: MutationWorkItem) -> None:
        if isinstance(item, MutationAction):
            self._verify_own_terminal(action=item)

        self._items.append(item)

    def _verify_own_terminal(self, *, action: MutationAction) -> None:
        if self._action_emitted:
            raise ValueError("An analyzer may emit only one action — its request's terminal.")

        self._action_emitted = True

        request: MutationRequest = self._request
        if isinstance(action, CreateMutationAction) and isinstance(request, CreateMutationRequest):
            if action.out is not request.out:
                raise ValueError(
                    "Emitted action does not produce its request's entity (out mismatch)."
                )

        elif isinstance(action, DeleteMutationAction) and isinstance(
            request, DeleteMutationRequest
        ):
            if action.target is not request.target:
                raise ValueError(
                    "Emitted action does not target its request's entity (target mismatch)."
                )

        else:
            raise ValueError("Emitted action's kind (create/delete) does not match its request.")
