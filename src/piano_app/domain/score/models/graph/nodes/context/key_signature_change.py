from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import Accidental, NoteName

from .base import ContextNode


# refactor needed
@dataclass(frozen=True, slots=True, kw_only=True)
class KeySignatureChange(ContextNode):
    accidental: Accidental = Accidental.NONE
    notes: tuple[NoteName, ...] = ()
