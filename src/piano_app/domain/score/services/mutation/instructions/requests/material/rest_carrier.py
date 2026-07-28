from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import RestCarrier
from piano_app.domain.score.models.notation import DottedRhythmicValue
from piano_app.domain.score.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRestCarrierRequest(CreateMutationRequest[RestCarrier]):
    """A request to create a rest carrier for a voice at a measure position."""

    voice: Voice
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRestCarrierRequest(DeleteMutationRequest[RestCarrier]):
    """A request to delete a rest carrier."""
