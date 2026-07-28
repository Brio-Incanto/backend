from piano_app.domain.score.models.material.carrier import (
    Carrier,
    NoteCarrier,
    RestCarrier,
)
from piano_app.domain.score.models.notation import DottedRhythmicValue, RhythmicSize
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.services.mutation.instructions import ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material.note_carrier import (
    CreateNoteCarrierAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material.note_carrier import (
    CreateNoteCarrierRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.rhythmic.leaf import (
    CreateLeafRhythmicContainerRequest,
)
from piano_app.domain.score.services.mutation.engine.scope import (
    EmitBuffer,
    PlanningScope,
)


# TODO add grace support, somehow resolve belonging to grace group
class CreateNoteCarrierAnalyzer:
    """Carrier level: replace an existing same-size leaf's carrier, or create a
    new leaf to host the carrier."""

    # TODO is broken, check anchor None before leaf
    def analyze(
        self,
        *,
        request: CreateNoteCarrierRequest,
        scope: PlanningScope,
    ) -> EmitBuffer:
        to_emit: EmitBuffer = EmitBuffer()

        anchor: TemporalAnchor | None = self._find_anchor(
            measure=request.measure,
            position=request.position,
        )
        leaf: LeafRhythmicContainer | None = (
            self._find_leaf(anchor=anchor, voice=request.voice) if anchor is not None else None
        )

        if leaf is not None and self._has_same_written_size(
            leaf=leaf,
            written_value=request.written_value,
        ):
            self._replace_on_leaf(into=to_emit, scope=scope, leaf=leaf, request=request)
        else:
            self._create_on_new_leaf(into=to_emit, scope=scope, request=request)

        return to_emit

    def _replace_on_leaf(
        self,
        *,
        into: EmitBuffer,
        scope: PlanningScope,
        leaf: LeafRhythmicContainer,
        request: CreateNoteCarrierRequest,
    ) -> None:
        carrier: Carrier | None = leaf.carrier
        if isinstance(carrier, NoteCarrier):
            scope.incorporate_delete(into=into, item=DeleteNoteCarrierRequest(note_carrier=carrier))
        elif isinstance(carrier, RestCarrier):
            scope.incorporate_delete(into=into, item=DeleteRestCarrierRequest(rest_carrier=carrier))

        scope.incorporate_create(
            into=into,
            item=CreateNoteCarrierAction(
                owner=leaf,
                articulation=request.articulation,
                out=request.out,
            ),
        )

    def _create_on_new_leaf(
        self,
        *,
        into: EmitBuffer,
        scope: PlanningScope,
        request: CreateNoteCarrierRequest,
    ) -> None:
        size: RhythmicSize = RhythmicSize(value=request.written_value, count=1)
        leaf_ref: ResultRef[LeafRhythmicContainer] = scope.incorporate_create(
            into=into,
            item=CreateLeafRhythmicContainerRequest(
                voice=request.voice,
                measure=request.measure,
                position=request.position,
                written_size=size,
                occupied_size=size,
                parent=None,
                out=ResultRef(),
            ),
        )
        scope.incorporate_create(
            into=into,
            item=CreateNoteCarrierAction(
                owner=leaf_ref,
                articulation=request.articulation,
                out=request.out,
            ),
        )

    def _find_anchor(
        self,
        *,
        measure: Measure,
        position: MeasurePosition,
    ) -> TemporalAnchor | None:
        return next(
            (anchor for anchor in measure.anchors if anchor.position == position),
            None,
        )

    def _find_leaf(
        self,
        *,
        anchor: TemporalAnchor,
        voice: Voice,
    ) -> LeafRhythmicContainer | None:
        return next(
            (leaf for leaf in anchor.leaf_containers if leaf.voice is voice),
            None,
        )

    def _has_same_written_size(
        self,
        *,
        leaf: LeafRhythmicContainer,
        written_value: DottedRhythmicValue,
    ) -> bool:
        return leaf.written_size.fraction == written_value.fraction
