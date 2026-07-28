from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)

from .handlers import MutationHandler
from .log import MutationLog
from .postprocessors import PlanPostprocessor
from .registry import MutationAnalyzerRegistry, MutationHandlerRegistry
from .resolver import Resolver
from .scope import EmitBuffer, PlanningScope
from .typing import PlanItem


class MutationEngine:
    """Drains a root request into ordered mutations, executing as it goes.

    Worklist over a stack: a popped request is handed to its analyzer and
    replaced by the items it emits; a popped action is executed **immediately**
    against the live model. Pushing emitted items reversed makes the LIFO stack
    preserve authoring order, so the analyzers' order *is* the execution order —
    the planner never reorders. Refs resolve from the run-time env at execution
    (the producer is popped before its consumer).

    One ``process`` call is one gesture and one transaction: a handler error
    rolls the whole gesture back through the log and re-raises; on success the
    log is the gesture's journal, ready for the undo stack.
    """

    def __init__(
        self,
        *,
        handler_registry: MutationHandlerRegistry,
        analyzer_registry: MutationAnalyzerRegistry,
        postprocessors: list[PlanPostprocessor],
    ) -> None:
        self._handler_registry: MutationHandlerRegistry = handler_registry
        self._analyzer_registry: MutationAnalyzerRegistry = analyzer_registry
        self._postprocessors: list[PlanPostprocessor] = postprocessors

    def process(self, *, request: MutationRequest) -> MutationLog:
        # scope, env and log are per-gesture: a fresh emit channel, run-time
        # environment and journal for this transaction.
        scope: PlanningScope = PlanningScope()
        resolver: Resolver = Resolver()
        log: MutationLog = MutationLog()

        stack: list[PlanItem] = [request]

        try:
            while stack:
                item: PlanItem = stack.pop()

                if isinstance(item, MutationAction):
                    self._execute(action=item, resolver=resolver, sink=log)
                    continue

                buffer: EmitBuffer = self._analyzer_registry.get(request_type=type(item)).analyze(
                    request=item, scope=scope
                )
                stack.extend(reversed(buffer.get_view()))

            # TODO run postprocessors to a fixpoint here
            # and idempotent — loop with an iter cap, reject on non-convergence.
        except Exception:
            log.rollback()
            raise

        return log

    def _execute(self, *, action: MutationAction, resolver: Resolver, sink: MutationSink) -> None:
        """Effect one action: dispatch to its handler, bind the produced entity
        into the run-time env under the action's ref."""
        handler: MutationHandler = self._handler_registry.get(action_type=type(action))
        produced: ScoreEntity | None = handler.handle(action=action, resolve=resolver, sink=sink)

        if produced is not None:
            resolver.register(ref=action.produced_ref, entity=produced)
