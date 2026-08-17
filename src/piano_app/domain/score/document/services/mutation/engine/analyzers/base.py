from typing import Protocol

from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import MutationRequest


class MutationAnalyzer[R: MutationRequest](Protocol):
    """Decomposes one request into ordered work items.

    An analyzer may emit further requests (recursive decomposition on *other*
    entities) and one terminal action on *its own* entity, into an ``EmitBuffer``
    it creates and returns. The order it returns items in is the execution order.
    To abort the whole gesture, raise ``MutationRejectedError``. An empty buffer
    is a legitimate no-op.
    """

    def analyze(self, *, request: R, resolver: ResolveBound) -> EmitBuffer: ...
