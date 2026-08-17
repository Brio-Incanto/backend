from itertools import chain

from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.helpers import find_anchor_at
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import MutationRejectedError
from piano_app.domain.score.document.services.mutation.instructions.actions.temporal import (
    CreateTemporalAnchorAction,
    DeleteTemporalAnchorAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    DeleteLeafRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
    DeleteTemporalAnchorRequest,
)


class CreateTemporalAnchorAnalyzer:
    """Decides whether an anchor may be created at the requested measure position.

    An existing anchor at that exact position rejects the request; otherwise a new
    anchor is created.
    """

    def analyze(
        self,
        *,
        request: CreateTemporalAnchorRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        # check if anchor already exists at requested position
        if (
            find_anchor_at(
                measure=request.measure,
                position=request.position,
            )
            is not None
        ):
            raise MutationRejectedError("Anchor already exists.")

        buffer.incorporate(
            item=CreateTemporalAnchorAction(
                measure=request.measure,
                position=request.position,
                out=request.out,
            ),
        )

        return buffer


class DeleteTemporalAnchorAnalyzer:
    """Decides the temporal anchor's deletion cascade.

    All attached metric leaves are deleted before the anchor; attached contexts
    are not handled yet.
    """

    def analyze(
        self,
        *,
        request: DeleteTemporalAnchorRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        anchor: TemporalAnchor = request.target

        for leaf in anchor.leaf_containers:
            buffer.incorporate(item=DeleteLeafRequest(target=leaf))

        # TODO later
        for _context in chain(anchor.starting_contexts, anchor.ending_contexts):
            pass

        buffer.incorporate(item=DeleteTemporalAnchorAction(target=anchor))

        return buffer
