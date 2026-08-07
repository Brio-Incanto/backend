from dataclasses import dataclass

from piano_app.domain.score.document.models.material import NoteCarrier
from piano_app.domain.score.document.models.notation import Articulation, DottedRhythmicValue
from piano_app.domain.score.document.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.document.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteCarrierRequest(CreateMutationRequest[NoteCarrier]):
    """A request to create a note carrier for a voice at a measure position."""

    voice: Voice
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    articulation: Articulation = Articulation.NONE


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteNoteCarrierRequest(DeleteMutationRequest[NoteCarrier]):
    """A request to delete a note carrier."""
