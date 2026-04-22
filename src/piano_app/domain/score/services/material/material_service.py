from piano_app.domain.score.models.graph.nodes.material import (
    Carrier,
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.models.graph.nodes.structural import (
    MeasureTimePoint,
    Staff,
    Voice,
)
from piano_app.domain.score.models.graph.notation import RhythmicValue
from piano_app.domain.score.services.cleanup import CleanupEngine
from piano_app.domain.score.services.cleanup.delete_request import DeleteRequest

from .graph_binder import MaterialGraphBinder
from .node_factory import MaterialNodeFactory


class MaterialService:
    def __init__(
        self,
        *,
        node_factory: MaterialNodeFactory,
        graph_binder: MaterialGraphBinder,
        cleanup_engine: CleanupEngine,
    ) -> None:
        self._node_factory: MaterialNodeFactory = node_factory
        self._graph_binder: MaterialGraphBinder = graph_binder
        self._cleanup_engine: CleanupEngine = cleanup_engine

    def insert_note(
        self,
        *,
        voice: Voice,
        staff: Staff,
        time_point: MeasureTimePoint,
        rhythmic_value: RhythmicValue,
        staff_step: int,
        dot_count: int = 0,
    ) -> tuple[SoundCarrier, Note]:
        carrier: SoundCarrier = self._node_factory.create_sound_carrier(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )
        note: Note = self._node_factory.create_note(
            staff_step=staff_step,
        )

        self._graph_binder.attach_note_to_sound_carrier(
            carrier=carrier,
            note=note,
        )
        self._graph_binder.attach_note_to_staff(
            note=note,
            staff=staff,
        )
        self._graph_binder.attach_carrier_to_voice(
            carrier=carrier,
            voice=voice,
        )
        self._graph_binder.attach_carrier_to_time_point(
            carrier=carrier,
            time_point=time_point,
        )

        return carrier, note

    def add_note_to_sound_carrier(
        self,
        *,
        carrier: SoundCarrier,
        staff: Staff,
        staff_step: int,
    ) -> Note:
        note: Note = self._node_factory.create_note(
            staff_step=staff_step,
        )

        self._graph_binder.attach_note_to_sound_carrier(
            carrier=carrier,
            note=note,
        )
        self._graph_binder.attach_note_to_staff(
            note=note,
            staff=staff,
        )

        return note

    def insert_rest(
        self,
        *,
        voice: Voice,
        staff: Staff,
        time_point: MeasureTimePoint,
        rhythmic_value: RhythmicValue,
        staff_step: int,
        dot_count: int = 0,
    ) -> tuple[RestCarrier, Rest]:
        carrier: RestCarrier = self._node_factory.create_rest_carrier(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )
        rest: Rest = self._node_factory.create_rest(
            staff_step=staff_step,
        )

        self._graph_binder.attach_rest_to_rest_carrier(
            carrier=carrier,
            rest=rest,
        )
        self._graph_binder.attach_rest_to_staff(
            rest=rest,
            staff=staff,
        )
        self._graph_binder.attach_carrier_to_voice(
            carrier=carrier,
            voice=voice,
        )
        self._graph_binder.attach_carrier_to_time_point(
            carrier=carrier,
            time_point=time_point,
        )

        return carrier, rest

    def delete_note(
        self,
        note: Note,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=note),
        )

    def delete_rest(
        self,
        rest: Rest,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=rest),
        )

    def delete_carrier(
        self,
        carrier: Carrier,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=carrier),
        )
