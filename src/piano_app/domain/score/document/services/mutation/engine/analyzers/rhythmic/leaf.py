from piano_app.domain.score.document.models.material import NoteCarrier, RestCarrier
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.models.structural.rhythm import (
    GroupRhythmicContainer,
    LeafRhythmicContainer,
    RhythmicContainer,
    RhythmicContainerParent,
)
from piano_app.domain.score.document.services.geometry import Point, Span, overflow
from piano_app.domain.score.document.services.geometry.score_geometry import ScoreGeometry
from piano_app.domain.score.document.services.helpers import find_anchor_at
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import (
    Bound,
    MutationRejectedError,
    ResultRef,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.rhythmic import (
    CreateLeafAction,
    DeleteLeafAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.material import (
    DeleteNoteCarrierRequest,
    DeleteRestCarrierRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    CreateLeafRequest,
    DeleteLeafRequest,
    DeleteRhythmicGroupRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
)


class CreateLeafAnalyzer:
    """Decides placement and displacement for a new metric leaf.

    Its start selects the deepest containing rhythmic scope; spilling across that
    scope rejects the request. The anchor is reused or created, and intersecting
    sibling containers are deleted before the leaf is created.
    """

    def analyze(
        self,
        *,
        request: CreateLeafRequest,
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
        else:
            anchor = ResultRef[TemporalAnchor]()
            buffer.incorporate(
                item=CreateTemporalAnchorRequest(
                    measure=request.measure,
                    position=request.position,
                    out=anchor,
                )
            )

        geometry: ScoreGeometry = ScoreGeometry(origin=request.measure)
        target: Point = Point(
            frame=geometry.of_measure(measure=request.measure),
            value=request.position.value,
        ).to(frame=geometry.root)

        # the descent restates the point in whatever scope holds it; the requested size
        # stays as written, since a size means the value written in the scope it lands in
        parent: RhythmicContainerParent
        local: Point
        parent, local = geometry.deepest_scope_at(point=target, voice=request.voice)
        placement: Span = Span(frame=local.frame, start=local.value, length=request.size.fraction)

        # geometry only reports how far the leaf outgrows its scope — refusing it is this
        # analyzer's own invariant, and it belongs here rather than down in the geometry
        if overflow(span=placement) > 0:
            raise MutationRejectedError("Leaf straddles a group boundary.")

        to_remove: list[RhythmicContainer] = [
            meeting.region for meeting in geometry.intersecting(span=placement, scope=parent)
        ]

        for item in to_remove:
            if isinstance(item, LeafRhythmicContainer):
                buffer.incorporate(item=DeleteLeafRequest(target=item))
            elif isinstance(item, GroupRhythmicContainer):
                buffer.incorporate(item=DeleteRhythmicGroupRequest(target=item))
            else:
                raise ValueError(f"Unknown container type: {type(item)}")

        buffer.incorporate(
            item=CreateLeafAction(
                parent=parent,
                anchor=anchor,
                size=request.size,
                out=request.out,
            ),
        )

        return buffer


class DeleteLeafAnalyzer:
    """Decides the metric leaf's deletion cascade.

    An attached note or rest carrier is deleted before the leaf; grace-group
    deletion is not implemented yet.
    """

    def analyze(
        self,
        *,
        request: DeleteLeafRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        leaf: LeafRhythmicContainer = request.target

        # TODO later
        if leaf.grace_before is not None:
            pass

        if leaf.grace_after is not None:
            pass

        carrier = leaf.carrier
        if carrier is not None:
            if isinstance(carrier, NoteCarrier):
                buffer.incorporate(item=DeleteNoteCarrierRequest(target=carrier))
            elif isinstance(carrier, RestCarrier):
                buffer.incorporate(item=DeleteRestCarrierRequest(target=carrier))
            else:
                raise ValueError(f"Unknown carrier type: {type(carrier)}")

        buffer.incorporate(item=DeleteLeafAction(target=leaf))

        return buffer
