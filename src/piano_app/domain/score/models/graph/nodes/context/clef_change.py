from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import Clef

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class ClefChange(ContextNode):
    clef: Clef
    octave_transposition: int = 0
