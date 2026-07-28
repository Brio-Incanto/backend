from typing import Protocol

from piano_app.domain.score.services.mutation.instructions import MutationRequest
from piano_app.domain.score.services.mutation.engine.scope import (
    EmitBuffer,
    PlanningScope,
)


class MutationAnalyzer[R: MutationRequest](Protocol):
    """Decomposes one request into ordered plan items.

    An analyzer may emit further requests (recursive decomposition on *other*
    entities), terminal actions on *its own* entity, and may intern shared
    producers through ``scope``. The order it returns items in is the execution
    order. To abort the whole plan, raise ``PlanRejectedError``; an empty list
    is a legitimate no-op.
    """

    def analyze(self, *, request: R, scope: PlanningScope) -> EmitBuffer: ...
