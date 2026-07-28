from dataclasses import dataclass

from piano_app.domain.score.models.material.primitive import Rest
from piano_app.domain.score.models.notation import DottedRhythmicValue
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    Voice,
)
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestRequest(CreateMutationRequest[Rest]):
    """A request to create a rest in a voice, on a staff, at a measure position."""

    voice: Voice
    staff: Staff
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    staff_step: int


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRestRequest(DeleteMutationRequest[Rest]):
    """A request to delete a rest."""
