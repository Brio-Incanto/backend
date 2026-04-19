from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import Articulation

from .base_carrier import Carrier


@dataclass(frozen=True, slots=True, kw_only=True)
class SoundCarrier(Carrier):
    articulation: Articulation = Articulation.NONE
