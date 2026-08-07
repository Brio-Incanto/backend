from dataclasses import dataclass

from piano_app.domain.score.document.models.material import Rest, RestCarrier
from piano_app.domain.score.document.models.structural import Staff
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)
from piano_app.domain.score.document.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestAction(CreateMutationAction[Rest]):
    """Creates a rest inside a rest carrier, on a staff."""

    rest_carrier: Bound[RestCarrier]
    staff: Staff
    staff_step: int


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRestAction(DeleteMutationAction[Rest]):
    """Deletes a rest."""
