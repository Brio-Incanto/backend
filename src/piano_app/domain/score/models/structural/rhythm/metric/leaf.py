from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import Carrier
from piano_app.domain.score.models.rhythmic.grace import GraceGroup

from .base import RhythmicContainer


@dataclass(slots=True, kw_only=True)
class LeafRhythmicContainer(RhythmicContainer):
    carrier: Carrier

    grace_before: GraceGroup | None = None
    grace_after: GraceGroup | None = None
