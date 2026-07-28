from piano_app.domain.score.models.material.carrier import (
    Carrier,
    NoteCarrier,
    RestCarrier,
)
from piano_app.domain.score.models.notation import Articulation, DottedRhythmicValue
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.services.helpers.hierarchy_traversal import flatten
from piano_app.domain.score.services.mutation.instructions import ResultRef
from piano_app.domain.score.services.mutation.instructions.actions.material.note import (
    CreateNoteAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    CreateNoteRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.material.note_carrier import (
    CreateNoteCarrierRequest,
)
from piano_app.domain.score.services.mutation.engine.scope import (
    EmitBuffer,
    PlanningScope,
)


class CreateNoteAnalyzer:
    """Creates a note for the requested voice / measure / position.

    Top of the create chain: it only asks whether it can chord-join an existing
    note carrier; everything else (the slot's size, neighbours) is delegated to
    the carrier request.
    """

    def analyze(
        self,
        *,
        request: CreateNoteRequest,
        scope: PlanningScope,
    ) -> EmitBuffer:
        to_emit: EmitBuffer = scope.create_buffer()

        anchor: TemporalAnchor | None = self._find_anchor(
            measure=request.measure,
            position=request.position,
        )

        if anchor is not None:
            leaf: LeafRhythmicContainer | None = self._find_leaf(
                anchor=anchor,
                voice=request.voice,
            )

            if leaf is not None and self._has_same_written_size(
                leaf=leaf,
                written_value=request.written_value,
            ):
                carrier: Carrier | None = leaf.carrier
                if isinstance(carrier, NoteCarrier):
                    self._chord_join(
                        buffer=to_emit,
                        note_carrier=carrier,
                        request=request,
                    )
                    return to_emit

                # TODO handle attachment to the existing leaf
                if not isinstance(carrier, RestCarrier):
                    raise ValueError(f"Unexpected carrier type: {type(carrier)}")

        self._create_note_on_new_carrier(
            buffer=to_emit,
            request=request,
        )
        return to_emit

    def _chord_join(
        self,
        *,
        buffer: EmitBuffer,
        note_carrier: NoteCarrier,
        request: CreateNoteRequest,
    ) -> None:
        buffer.incorporate_create(
            item=CreateNoteAction(
                note_carrier=note_carrier,
                staff=request.staff,
                staff_step=request.staff_step,
                pitch=request.pitch,
                fingering=request.fingering,
            ),
        )

    def _create_note_on_new_carrier(
        self,
        *,
        buffer: EmitBuffer,
        request: CreateNoteRequest,
    ) -> None:
        carrier_ref: ResultRef[NoteCarrier] = buffer.incorporate_create(
            item=CreateNoteCarrierRequest(
                voice=request.voice,
                measure=request.measure,
                position=request.position,
                written_value=request.written_value,
                articulation=Articulation.NONE,
                out=ResultRef(),
            ),
        )
        buffer.incorporate_create(
            item=CreateNoteAction(
                note_carrier=carrier_ref,
                staff=request.staff,
                staff_step=request.staff_step,
                pitch=request.pitch,
                fingering=request.fingering,
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
            (leaf for leaf in flatten(voice) if leaf.anchor is anchor),
            None,
        )

    def _has_same_written_size(
        self,
        *,
        leaf: LeafRhythmicContainer,
        written_value: DottedRhythmicValue,
    ) -> bool:
        return leaf.written_size.value == written_value and leaf.written_size.count == 1
