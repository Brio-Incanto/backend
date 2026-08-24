from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

from ..base import Context

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class SpanContext(Context):
    """A context that occupies a range — adds ``end`` on top of ``Context.start``."""

    end: TemporalAnchor

    def __post_init__(self) -> None:
        if self.start is self.end:
            raise ValueError("Start and end must be different anchors.")

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        self.end.add_ending_context(context=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.end.remove_ending_context(context=self, sink=sink)
        super().detach(sink=sink)
