from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import Accidental, Clef
from piano_app.domain.shared.abstract import abstract

from .base import PointContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import Staff, TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class StaffPointContext(PointContext):
    """A point context scoped to one staff."""

    staff: Staff

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        self.staff.add_context(context=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.staff.remove_context(context=self, sink=sink)
        super().detach(sink=sink)


# How far a clef marking may shift the staff, in octaves (8va/15va up or down) --
# tunable, but a bound belongs here, not left wide open to any int.
_MAX_CLEF_OCTAVE_TRANSPOSITION: int = 2


@dataclass(slots=True, kw_only=True, eq=False)
class ClefChange(StaffPointContext):
    clef: Clef
    octave_transposition: int = 0

    def __post_init__(self) -> None:
        if abs(self.octave_transposition) > _MAX_CLEF_OCTAVE_TRANSPOSITION:
            raise ValueError(
                f"Octave transposition must be within "
                f"{_MAX_CLEF_OCTAVE_TRANSPOSITION} octaves (8va/15va)."
            )

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        staff: Staff,
        clef: Clef,
        octave_transposition: int = 0,
        sink: MutationSink = DIRECT_SINK,
    ) -> ClefChange:
        clef_change: ClefChange = cls(
            start=start,
            staff=staff,
            clef=clef,
            octave_transposition=octave_transposition,
        )
        clef_change.attach(sink=sink)
        return clef_change

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        staff: Staff,
        clef: Clef,
        octave_transposition: int = 0,
        sink: MutationSink = DIRECT_SINK,
    ) -> ClefChange:
        clef_change: ClefChange = cls(
            id=id,
            start=start,
            staff=staff,
            clef=clef,
            octave_transposition=octave_transposition,
        )
        clef_change.attach(sink=sink)
        return clef_change


@dataclass(frozen=True, slots=True, kw_only=True)
class KeySignatureSymbol:
    staff_step: int
    accidental: Accidental

    def __post_init__(self) -> None:
        if self.accidental is Accidental.NONE:
            raise ValueError("A key signature symbol must assert an actual accidental.")


@dataclass(slots=True, kw_only=True, eq=False)
class KeySignatureChange(StaffPointContext):
    symbols: tuple[KeySignatureSymbol, ...] = ()

    def __post_init__(self) -> None:
        steps: list[int] = [symbol.staff_step for symbol in self.symbols]
        if len(steps) != len(set(steps)):
            raise ValueError("Key signature symbols must not repeat a staff step.")

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        staff: Staff,
        symbols: tuple[KeySignatureSymbol, ...] = (),
        sink: MutationSink = DIRECT_SINK,
    ) -> KeySignatureChange:
        key_signature_change: KeySignatureChange = cls(start=start, staff=staff, symbols=symbols)
        key_signature_change.attach(sink=sink)
        return key_signature_change

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        staff: Staff,
        symbols: tuple[KeySignatureSymbol, ...] = (),
        sink: MutationSink = DIRECT_SINK,
    ) -> KeySignatureChange:
        key_signature_change: KeySignatureChange = cls(
            id=id,
            start=start,
            staff=staff,
            symbols=symbols,
        )
        key_signature_change.attach(sink=sink)
        return key_signature_change
