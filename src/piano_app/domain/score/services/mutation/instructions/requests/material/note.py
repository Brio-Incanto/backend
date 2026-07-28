from dataclasses import dataclass, field

from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.notation import (
    DottedRhythmicValue,
    Fingering,
    Pitch,
)
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    Voice,
)
from piano_app.domain.score.services.mutation.instructions import ResultRef
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    MutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteRequest(MutationRequest):
    voice: Voice
    staff: Staff
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    staff_step: int
    pitch: Pitch

    fingering: Fingering = Fingering.NONE

    out: ResultRef[Note] = field(default_factory=ResultRef)

    @property
    def produced_ref(self) -> ResultRef[Note]:
        return self.out
