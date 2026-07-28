from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.material.primitive import Rest
from piano_app.domain.score.models.structural import Staff
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
)
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestAction(CreateMutationAction[Rest]):
    """Creates a rest inside a rest carrier, on a staff."""

    rest_carrier: Bound[RestCarrier]
    staff: Staff
    staff_step: int
