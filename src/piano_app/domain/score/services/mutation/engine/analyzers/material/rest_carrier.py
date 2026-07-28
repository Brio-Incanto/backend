from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.models.notation import RhythmicSize
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.services.mutation.instructions import ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material.rest_carrier import (
    CreateRestCarrierAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material.rest_carrier import (
    CreateRestCarrierRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.rhythmic.leaf import (
    CreateLeafRhythmicContainerRequest,
)
from piano_app.domain.score.services.mutation.engine.scope import (
    EmitBuffer,
    PlanningScope,
)


class CreateRestCarrierAnalyzer:
    """Creates a rest carrier on a leaf, finding or creating the leaf first.

    TODO: emit the ``CreateRestAction`` for the rest inside the carrier — it
    needs ``staff`` / ``staff_step``, which ``CreateRestCarrierRequest`` does
    not yet carry (pending the fill staff-policy decision). A rest carrier is
    meaningless without its rest, so this is incomplete until that is settled.
    """

    def analyze(
        self,
        *,
        request: CreateRestCarrierRequest,
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

        owner: CarrierOwner | ResultRef[LeafRhythmicContainer]
        if leaf is not None:
            owner = leaf
        else:
            owner = scope.incorporate_create(
                into=to_emit, item=self._leaf_request(request=request, out=ResultRef())
            )

        scope.incorporate_create(
            into=to_emit, item=CreateRestCarrierAction(owner=owner, out=request.out)
        )
        return to_emit

    def _leaf_request(
        self,
        *,
        request: CreateRestCarrierRequest,
        out: ResultRef[LeafRhythmicContainer],
    ) -> CreateLeafRhythmicContainerRequest:
        size: RhythmicSize = RhythmicSize(value=request.written_value, count=1)
        return CreateLeafRhythmicContainerRequest(
            voice=request.voice,
            measure=request.measure,
            position=request.position,
            written_size=size,
            occupied_size=size,
            parent=None,
            out=out,
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
