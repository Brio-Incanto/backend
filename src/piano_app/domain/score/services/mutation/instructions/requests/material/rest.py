from dataclasses import dataclass, field

from piano_app.domain.score.models.material.primitive import Rest
from piano_app.domain.score.models.notation import DottedRhythmicValue
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
class CreateRestRequest(MutationRequest):
    voice: Voice
    staff: Staff
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    staff_step: int

    out: ResultRef[Rest] = field(default_factory=ResultRef)

    @property
    def produced_ref(self) -> ResultRef[Rest]:
        return self.out
