from piano_app.domain.score.document.models.context import KeySignatureChange
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.helpers import (
    find_anchor_at,
    find_staff_point_context_at,
)
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    CreateKeySignatureChangeAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.context import (
    CreateKeySignatureChangeRequest,
    DeleteContextRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
)


class CreateKeySignatureChangeAnalyzer:
    """Decides placement and displacement for a new key signature change.

    Same shape as ``CreateClefChangeAnalyzer`` — the anchor is reused or created,
    and a key signature already asserted on the same staff at that anchor is
    replaced, not rejected.
    """

    def analyze(
        self,
        *,
        request: CreateKeySignatureChangeRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        existing_anchor: TemporalAnchor | None = find_anchor_at(
            measure=request.measure,
            position=request.position,
        )

        anchor: Bound[TemporalAnchor]
        if existing_anchor is not None:
            anchor = existing_anchor

            conflicting: KeySignatureChange | None = find_staff_point_context_at(
                anchor=existing_anchor,
                context_type=KeySignatureChange,
                staff=request.staff,
            )
            if conflicting is not None:
                buffer.incorporate(item=DeleteContextRequest(target=conflicting))
        else:
            anchor = ResultRef[TemporalAnchor]()
            buffer.incorporate(
                item=CreateTemporalAnchorRequest(
                    measure=request.measure,
                    position=request.position,
                    out=anchor,
                )
            )

        buffer.incorporate(
            item=CreateKeySignatureChangeAction(
                start=anchor,
                staff=request.staff,
                symbols=request.symbols,
                out=request.out,
            ),
        )

        return buffer
