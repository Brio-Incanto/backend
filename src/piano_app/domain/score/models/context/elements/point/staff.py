from dataclasses import dataclass

from piano_app.domain.score.models.context.elements.base import ContextElement
from piano_app.domain.score.models.notation import Accidental, Clef


@dataclass(slots=True, kw_only=True, eq=False)
class StaffPointContextElement(ContextElement):
    pass


@dataclass(slots=True, kw_only=True, eq=False)
class ClefChange(StaffPointContextElement):
    clef: Clef
    octave_transposition: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class KeySignatureSymbol:
    staff_step: int
    accidental: Accidental


@dataclass(slots=True, kw_only=True, eq=False)
class KeySignatureChange(StaffPointContextElement):
    symbols: tuple[KeySignatureSymbol, ...] = ()
