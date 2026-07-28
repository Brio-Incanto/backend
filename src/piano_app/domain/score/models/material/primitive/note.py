from dataclasses import dataclass

from piano_app.domain.score.models.notation import Accidental, Fingering


@dataclass(frozen=True, slots=True, kw_only=True)
class Note(StaffElement):
    accidental: Accidental = Accidental.NONE
    fingering: Fingering = Fingering.NONE
