from dataclasses import dataclass, field

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.notation import Articulation, DottedRhythmicValue
from piano_app.domain.score.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    MutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteCarrierRequest(MutationRequest):
    voice: Voice
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    articulation: Articulation = Articulation.NONE

    out: ResultRef[NoteCarrier] = field(default_factory=ResultRef)

    @property
    def produced_ref(self) -> ResultRef[NoteCarrier]:
        return self.out
