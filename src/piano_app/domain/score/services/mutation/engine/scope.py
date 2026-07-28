from collections.abc import Hashable, Sequence
from typing import Any

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions import (
    MutationRequest,
    ResultRef,
)

from .typing import PlanItem


class _ScopeEntry:
    """A single entry in the scope that holds ref and landed flag.
    Landed is used to distinguish what has already been emitted
    (only request - False, request and action - True).
    """

    def __init__(self, *, ref: ResultRef[Any] | None) -> None:
        self.ref: ResultRef[Any] | None = ref
        self.landed: bool = False

    def land(self) -> None:
        self.landed = True


class PlanningScope:
    """Scope to track operations on entities with identities through one run of planner."""

    # stores a ref if exists, None if is deleted
    def __init__(self) -> None:
        self._refs: dict[Hashable, _ScopeEntry] = {}

    def create_buffer(self) -> EmitBuffer:
        return EmitBuffer(refs=self._refs)


class EmitBuffer:
    """Buffer to store plan items per analyzer entry.
    To add a new item to the buffer, use ``incorporate_create`` or ``incorporate_delete``.
    Decision about addition is based on the refs from planning scope.
    """

    def __init__(self, *, refs: dict[Hashable, _ScopeEntry]) -> None:
        self._items: list[PlanItem] = []

        self._refs: dict[Hashable, _ScopeEntry] = refs

    def get_view(self) -> Sequence[PlanItem]:
        return self._items

    # it is assumed that returned refs are used to make chains of refs
    def incorporate_create[T: ScoreEntity](
        self,
        *,
        item: PlanItem,
    ) -> ResultRef[T]:
        # must not be None for create
        ref: ResultRef[T] | None = item.produced_ref
        if ref is None:
            raise ValueError("Cannot incorporate a create item without a produced ref.")

        # if the entity is not identifiable, always emit it
        key: Hashable | None = item.identity_key
        if key is None:
            self._items.append(item)
            return ref

        # check if identity is already in scope
        if key in self._refs:
            existing: _ScopeEntry = self._refs[key]

            # identity is in the delete state
            if existing.ref is None:
                # request branch
                if isinstance(item, MutationRequest):
                    # catch it here rather than when the delete action is received and raises
                    if not existing.landed:
                        raise ValueError("Replace received before delete action landed")

                    # replace delete with create at the stage of request
                    self._refs[key] = _ScopeEntry(ref=ref)
                    self._items.append(item)
                    return ref

                # action branch
                # action must not be added before a request for it
                raise ValueError("Action is received before request")

            # identity is in the create state
            # request branch
            if isinstance(item, MutationRequest):
                # return already existing ref to deduplicate
                return existing.ref

            # action branch
            # the first action for that request, set landed and return ref
            if not existing.landed:
                # to prevent emitting action that breaks the chain of refs
                if existing.ref is not ref:  # identity check because the same object must be passed
                    raise ValueError("Ref in Action and in Request are different")

                existing.land()
                self._items.append(item)
                return existing.ref

            # raise because for actions it is probably a bug
            # probably multiple create actions for the same entity within one analyzer
            raise ValueError("Multiple create actions for the same entity")

        # request branch
        # the first request for that entity, set and return
        if isinstance(item, MutationRequest):
            self._refs[key] = _ScopeEntry(ref=ref)
            self._items.append(item)
            return ref

        # action branch
        # action must not be added before a request for it
        raise ValueError("Action is received before request")

    def incorporate_delete(
        self,
        *,
        item: PlanItem,
    ) -> None:
        # must be None for delete
        ref: ResultRef[Any] | None = item.produced_ref
        if ref is not None:
            raise ValueError("Cannot incorporate a delete item with a produced ref.")

        # if the entity is not identifiable, always emit it
        key: Hashable | None = item.identity_key
        if key is None:
            self._items.append(item)
            return

        # check if identity is already in scope
        if key in self._refs:
            existing: _ScopeEntry = self._refs[key]

            # identity is in the create state
            if existing.ref is not None:
                # request branch
                if isinstance(item, MutationRequest):
                    # catch it here rather than when the create action is received and raises
                    if not existing.landed:
                        raise ValueError("Replace received before create action landed")

                    self._refs[key] = _ScopeEntry(ref=None)
                    self._items.append(item)
                    return

                # action branch
                # action must not be added before a request for it
                raise ValueError("Action is received before request")

            # identity is in the delete state
            # request branch
            if isinstance(item, MutationRequest):
                # return already existing ref to deduplicate
                return

            # action branch
            # the first action for that request, set landed and return ref
            if not existing.landed:
                existing.land()
                self._items.append(item)
                return

            # raise because for actions it is probably a bug
            # probably multiple delete actions for the same entity within one analyzer
            # or called from the other analyzer directly instead of requesting
            raise ValueError("Multiple delete actions for the same entity")

        # request branch
        # the first request for that entity, set and return
        if isinstance(item, MutationRequest):
            self._refs[key] = _ScopeEntry(ref=None)
            self._items.append(item)
            return

        # action branch
        # action must not be added before a request for it
        raise ValueError("Action is received before request")
