from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestCarrierAction(CreateMutationAction[RestCarrier]):
    """Creates a rest carrier on its owner (leaf or grace item)."""

    owner: Bound[CarrierOwner]


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRestCarrierAction(DeleteMutationAction[RestCarrier]):
    """Deletes a rest carrier."""
