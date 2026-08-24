from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

from .base import SpanContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class ScoreSpanContext(SpanContext):
    """A span context scoped to the whole score."""


@dataclass(slots=True, kw_only=True, eq=False)
class SustainHold(ScoreSpanContext):
    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        end: TemporalAnchor,
        sink: MutationSink = DIRECT_SINK,
    ) -> SustainHold:
        sustain_hold: SustainHold = cls(start=start, end=end)
        sustain_hold.attach(sink=sink)
        return sustain_hold

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        end: TemporalAnchor,
        sink: MutationSink = DIRECT_SINK,
    ) -> SustainHold:
        sustain_hold: SustainHold = cls(id=id, start=start, end=end)
        sustain_hold.attach(sink=sink)
        return sustain_hold
