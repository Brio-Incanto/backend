from piano_app.domain.score.document.models.context import ClefChange
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.helpers import (
    find_anchor_at,
    find_staff_point_context_at,
)
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import Bound, ResultRef
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    CreateClefChangeAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.context import (
    CreateClefChangeRequest,
    DeleteContextRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
)


class CreateClefChangeAnalyzer:
    """Decides placement and displacement for a new clef change.

    The anchor is reused or created, exactly like a metric leaf. A clef change
    already asserted on the same staff at that anchor is replaced, not rejected —
    "set a new clef here" reads as a replacement, not an error, the same way
    inserting a note into an occupied slot does.
    """

    def analyze(
        self,
        *,
        request: CreateClefChangeRequest,
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

            # a freshly created anchor cannot already hold a conflicting context --
            # the search only makes sense against one that already existed
            conflicting: ClefChange | None = find_staff_point_context_at(
                anchor=existing_anchor,
                context_type=ClefChange,
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
            item=CreateClefChangeAction(
                start=anchor,
                staff=request.staff,
                clef=request.clef,
                octave_transposition=request.octave_transposition,
                out=request.out,
            ),
        )

        return buffer
