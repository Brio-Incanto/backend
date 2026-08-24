from dataclasses import dataclass

from piano_app.domain.score.document.models.context import KeySignatureChange, KeySignatureSymbol
from piano_app.domain.score.document.models.structural import Measure, MeasurePosition, Staff
from piano_app.domain.score.document.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateKeySignatureChangeRequest(CreateMutationRequest[KeySignatureChange]):
    """A request to assert a key signature on one staff, starting at a measure
    position."""

    measure: Measure
    position: MeasurePosition
    staff: Staff
    symbols: tuple[KeySignatureSymbol, ...] = ()
