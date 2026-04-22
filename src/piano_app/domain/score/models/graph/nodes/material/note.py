from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import Accidental, Fingering

from .staff_element import StaffElement


@dataclass(frozen=True, slots=True, kw_only=True)
class Note(StaffElement):
    accidental: Accidental = Accidental.NONE
    fingering: Fingering = Fingering.NONE
