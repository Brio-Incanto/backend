from dataclasses import dataclass

from piano_app.domain.score.document.models import ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class Relation(ScoreEntity):
    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        raise NotImplementedError

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        raise NotImplementedError
