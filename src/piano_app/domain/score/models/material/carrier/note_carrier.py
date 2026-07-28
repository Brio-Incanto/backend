from dataclasses import dataclass

from piano_app.domain.score.models.material.primitive.note import Note
from piano_app.domain.score.models.notation import Articulation

from .base import Carrier


@dataclass(slots=True, kw_only=True)
class SoundCarrier(Carrier):
    notes: list[Note]
    articulation: Articulation = Articulation.NONE

    def __post_init__(self) -> None:
        if not self.notes:
            raise ValueError("SoundCarrier must contain at least one note.")
