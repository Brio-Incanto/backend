from dataclasses import dataclass

from piano_app.domain.score.models.material.primitive.rest import Rest

from .base import Carrier


@dataclass(slots=True, kw_only=True)
class RestCarrier(Carrier):
    rest: Rest
