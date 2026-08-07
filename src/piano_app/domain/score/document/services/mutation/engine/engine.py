from collections.abc import Sequence

from piano_app.domain.score.document.models import ScoreDocument, ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)

from .buffer import EmitBuffer
from .handlers import MutationHandler
from .log import MutationLog
from .postprocessors import MutatedStatePostprocessor
from .registry import MutationAnalyzerRegistry, MutationHandlerRegistry
from .resolver import Resolver
from .typing import MutationWorkItem


class MutationEngine:
    """Drains a root request into ordered mutations, executing as it goes.

    Worklist over a stack: a popped request is handed to its analyzer and
    replaced by the items it emits; a popped action is executed **immediately**
    against the live model. Pushing emitted items reversed makes the LIFO stack
    preserve authoring order, so the analyzers' order *is* the execution order —
    the engine never reorders. Refs resolve from the run-time env at execution
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
        postprocessors: list[MutatedStatePostprocessor],
    ) -> None:
        self._handler_registry: MutationHandlerRegistry = handler_registry
        self._analyzer_registry: MutationAnalyzerRegistry = analyzer_registry
        self._postprocessors: list[MutatedStatePostprocessor] = postprocessors

    # TODO consider adding convergence checking
    def process(
        self, *, document: ScoreDocument, requests: Sequence[MutationRequest]
    ) -> MutationLog:
        # env and log are per-gesture: a fresh run-time environment and journal
        # for this transaction.
        resolver: Resolver = Resolver()
        log: MutationLog = MutationLog()

        # TODO run tests to check how works with transitional state
        try:
            self._drain(requests=requests, resolver=resolver, log=log)

            fixes_produced: bool = True
            while fixes_produced:
                fixes_produced = False

                for postprocessor in self._postprocessors:
                    fix_requests: Sequence[MutationRequest] = postprocessor.search_fixes(
                        document=document,
                    )

                    # set the flag and prevent passing empty list to _drain
                    if fix_requests:
                        fixes_produced = True
                        self._drain(requests=fix_requests, resolver=resolver, log=log)

        except Exception:
            log.rollback()
            raise

        return log

    def _drain(
        self, *, requests: Sequence[MutationRequest], resolver: Resolver, log: MutationLog
    ) -> None:
        """Unfolds a request into a tree and executes as it unfolds.
        Actions are leaves of the tree, requests are internal nodes.
        """
        stack: list[MutationWorkItem] = list(reversed(requests))

        while stack:
            item: MutationWorkItem = stack.pop()

            if isinstance(item, MutationAction):
                self._execute(action=item, resolver=resolver, sink=log)
                continue

            buffer: EmitBuffer = self._analyzer_registry.get(request_type=type(item)).analyze(
                request=item,
                resolver=resolver,
            )
            stack.extend(reversed(buffer.items))

    def _execute(self, *, action: MutationAction, resolver: Resolver, sink: MutationSink) -> None:
        """Executes a single action, checks its type, validates the expected output,
        and registers in resolver if something is produced.
        """
        handler: MutationHandler[MutationAction] = self._handler_registry.get(
            action_type=type(action)
        )
        produced: ScoreEntity | None = handler.handle(action=action, resolve=resolver, sink=sink)

        if isinstance(action, CreateMutationAction):
            if produced is None:
                raise ValueError(f"Create handler produced nothing: {type(action).__name__}.")

            resolver.register(reference=action.produced_ref, entity=produced)

        elif isinstance(action, DeleteMutationAction):
            if produced is not None:
                raise ValueError(f"Delete handler produced an entity: {type(action).__name__}.")

        else:
            raise ValueError(f"Action is neither create nor delete: {type(action).__name__}.")
