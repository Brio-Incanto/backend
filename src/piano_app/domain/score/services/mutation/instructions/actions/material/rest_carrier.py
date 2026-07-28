from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
)
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestCarrierAction(CreateMutationAction[RestCarrier]):
    """Creates a rest carrier on its owner (leaf or grace item)."""

    owner: Bound[CarrierOwner]
