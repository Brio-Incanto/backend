from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

from .base import SpanContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import Staff, TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class StaffSpanContext(SpanContext):
    """A span context scoped to one staff."""

    staff: Staff

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        self.staff.add_context(context=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.staff.remove_context(context=self, sink=sink)
        super().detach(sink=sink)


@dataclass(slots=True, kw_only=True, eq=False)
class OctaveTransposition(StaffSpanContext):
    """How far the written notes in this span sound transposed — an 8va/15va
    bracket. ``octaves`` is signed: positive sounds higher than written."""

    octaves: int

    def __post_init__(self) -> None:
        super().__post_init__()

        if not 1 <= abs(self.octaves) <= 2:
            raise ValueError(
                "Octave transposition must be 1 or 2 octaves (8va/15va), up or down."
            )

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        end: TemporalAnchor,
        staff: Staff,
        octaves: int,
        sink: MutationSink = DIRECT_SINK,
    ) -> OctaveTransposition:
        octave_transposition: OctaveTransposition = cls(
            start=start,
            end=end,
            staff=staff,
            octaves=octaves,
        )
        octave_transposition.attach(sink=sink)
        return octave_transposition

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        end: TemporalAnchor,
        staff: Staff,
        octaves: int,
        sink: MutationSink = DIRECT_SINK,
    ) -> OctaveTransposition:
        octave_transposition: OctaveTransposition = cls(
            id=id,
            start=start,
            end=end,
            staff=staff,
            octaves=octaves,
        )
        octave_transposition.attach(sink=sink)
        return octave_transposition
