from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.base import ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class Context(ScoreEntity):
    """Role base: an event placed directly on the timeline.

    Unlike ``Relation``, a context IS its own placement — position lives on the
    concrete subclass itself, not behind a separate wrapper entity. Every context
    starts somewhere; ``SpanContext`` additionally ends somewhere.
    """

    start: TemporalAnchor

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.start.add_starting_context(context=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self.start.remove_starting_context(context=self, sink=sink)
