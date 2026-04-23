from piano_app.domain.score.models.graph import EdgeRelation
from piano_app.domain.score.models.graph.nodes.context import (
    ClefChange,
    DynamicChange,
    KeySignatureChange,
    TempoChange,
    TimeSignatureChange,
)
from piano_app.domain.score.models.graph.nodes.structural import (
    Measure,
    MeasureTimePoint,
    Staff,
    Voice,
)
from piano_app.domain.score.services.graph_service import GraphService


class ContextGraphBinder:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    def attach_clef_change_to_staff(
        self,
        *,
        clef_change: ClefChange,
        staff: Staff,
    ) -> None:
        existing_staffs: list[Staff] = self._graph_service.target_nodes_of_type(
            node=clef_change,
            node_type=Staff,
            relation=EdgeRelation.BELONGS_TO,
        )
        if existing_staffs:
            raise ValueError(f"ClefChange {clef_change} already belongs to a Staff")

        self._graph_service.connect(
            source=clef_change,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_clef_change_to_time_point(
        self,
        *,
        clef_change: ClefChange,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_time_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=clef_change,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if existing_time_points:
            raise ValueError(
                f"ClefChange {clef_change} already starts at a MeasureTimePoint"
            )

        self._graph_service.connect(
            source=clef_change,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )

    def attach_dynamic_change_to_voice(
        self,
        *,
        dynamic_change: DynamicChange,
        voice: Voice,
    ) -> None:
        self._graph_service.connect(
            source=dynamic_change,
            target=voice,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_dynamic_change_to_time_point(
        self,
        *,
        dynamic_change: DynamicChange,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_time_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=dynamic_change,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if existing_time_points:
            raise ValueError(
                f"DynamicChange {dynamic_change} already starts at a MeasureTimePoint"
            )

        self._graph_service.connect(
            source=dynamic_change,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )

    def attach_key_signature_change_to_staff(
        self,
        *,
        key_signature_change: KeySignatureChange,
        staff: Staff,
    ) -> None:
        existing_staffs: list[Staff] = self._graph_service.target_nodes_of_type(
            node=key_signature_change,
            node_type=Staff,
            relation=EdgeRelation.BELONGS_TO,
        )
        if existing_staffs:
            raise ValueError(
                f"KeySignatureChange {key_signature_change} already belongs to a Staff"
            )

        self._graph_service.connect(
            source=key_signature_change,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_key_signature_change_to_time_point(
        self,
        *,
        key_signature_change: KeySignatureChange,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_time_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=key_signature_change,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if existing_time_points:
            raise ValueError(
                f"KeySignatureChange {key_signature_change} already "
                f"starts at a MeasureTimePoint"
            )

        self._graph_service.connect(
            source=key_signature_change,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )

    def attach_tempo_change_to_time_point(
        self,
        *,
        tempo_change: TempoChange,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_time_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=tempo_change,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if existing_time_points:
            raise ValueError(
                f"TempoChange {tempo_change} already starts at a MeasureTimePoint"
            )

        attached_tempo_changes: list[TempoChange] = (
            self._graph_service.source_nodes_of_type(
                node=time_point,
                node_type=TempoChange,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if attached_tempo_changes:
            raise ValueError(
                f"MeasureTimePoint {time_point} already has a tempo change"
            )

        self._graph_service.connect(
            source=tempo_change,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )

    def attach_time_signature_change_to_measure(
        self,
        *,
        time_signature_change: TimeSignatureChange,
        measure: Measure,
    ) -> None:
        existing_measures: list[Measure] = self._graph_service.target_nodes_of_type(
            node=time_signature_change,
            node_type=Measure,
            relation=EdgeRelation.STARTS_AT,
        )
        if existing_measures:
            raise ValueError(
                f"TimeSignatureChange {time_signature_change} already "
                f"starts at a Measure"
            )

        attached_time_signature_changes: list[TimeSignatureChange] = (
            self._graph_service.source_nodes_of_type(
                node=measure,
                node_type=TimeSignatureChange,
                relation=EdgeRelation.STARTS_AT,
            )
        )
        if attached_time_signature_changes:
            raise ValueError(f"Measure {measure} already has a time signature change")

        self._graph_service.connect(
            source=time_signature_change,
            target=measure,
            relation=EdgeRelation.STARTS_AT,
        )
