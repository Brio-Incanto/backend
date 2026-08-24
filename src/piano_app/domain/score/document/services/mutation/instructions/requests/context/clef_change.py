from dataclasses import dataclass

from piano_app.domain.score.document.models.context import ClefChange
from piano_app.domain.score.document.models.notation import Clef
from piano_app.domain.score.document.models.structural import Measure, MeasurePosition, Staff
from piano_app.domain.score.document.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateClefChangeRequest(CreateMutationRequest[ClefChange]):
    """A request to assert a clef on one staff, starting at a measure position."""

    measure: Measure
    position: MeasurePosition
    staff: Staff
    clef: Clef
    octave_transposition: int = 0
