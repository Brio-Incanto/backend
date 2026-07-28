from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.notation import DottedRhythmicValue


@dataclass(slots=True, kw_only=True)
class GraceItem:
    rhythmic_value: DottedRhythmicValue
    note_carrier: NoteCarrier
