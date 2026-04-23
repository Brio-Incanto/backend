from piano_app.domain.score.models.graph import EdgeRelation
from piano_app.domain.score.models.graph.nodes.structural import (
    Measure,
    MeasureTimePoint,
)
from piano_app.domain.score.services.graph_service import GraphService


class StructuralGraphBinder:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    def attach_time_point_to_measure(
        self,
        *,
        measure: Measure,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_measures: list[Measure] = self._graph_service.source_nodes_of_type(
            node=time_point,
            node_type=Measure,
            relation=EdgeRelation.CONTAINS,
        )
        if existing_measures:
            raise ValueError(
                f"MeasureTimePoint {time_point} already belongs to a Measure"
            )

        self._graph_service.connect(
            source=measure,
            target=time_point,
            relation=EdgeRelation.CONTAINS,
        )

    def attach_next_measure(
        self,
        *,
        source_measure: Measure,
        target_measure: Measure,
    ) -> None:
        # may change with the introduction of navigation
        existing_next_measures: list[Measure] = (
            self._graph_service.target_nodes_of_type(
                node=source_measure,
                node_type=Measure,
                relation=EdgeRelation.PRECEDES,
            )
        )
        if existing_next_measures:
            raise ValueError(f"Measure {source_measure} already has a next measure")

        existing_previous_measures: list[Measure] = (
            self._graph_service.source_nodes_of_type(
                node=target_measure,
                node_type=Measure,
                relation=EdgeRelation.PRECEDES,
            )
        )
        if existing_previous_measures:
            raise ValueError(f"Measure {target_measure} already has a previous measure")

        self._graph_service.connect(
            source=source_measure,
            target=target_measure,
            relation=EdgeRelation.PRECEDES,
        )

    def attach_next_time_point(
        self,
        *,
        source_time_point: MeasureTimePoint,
        target_time_point: MeasureTimePoint,
    ) -> None:
        source_measures: list[Measure] = self._graph_service.source_nodes_of_type(
            node=source_time_point,
            node_type=Measure,
            relation=EdgeRelation.CONTAINS,
        )
        if not source_measures:
            raise ValueError(
                f"Source time point {source_time_point} does not belong to a Measure."
            )

        target_measures: list[Measure] = self._graph_service.source_nodes_of_type(
            node=target_time_point,
            node_type=Measure,
            relation=EdgeRelation.CONTAINS,
        )
        if not target_measures:
            raise ValueError(
                f"Target time point {target_time_point} does not belong to a Measure."
            )

        source_measure: Measure = source_measures[0]
        target_measure: Measure = target_measures[0]

        if source_measure != target_measure:
            raise ValueError("Time points must belong to the same measure.")

        existing_next_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=source_time_point,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.PRECEDES,
            )
        )
        if existing_next_points:
            raise ValueError(
                f"MeasureTimePoint {source_time_point} already has a next time point"
            )

        existing_previous_points: list[MeasureTimePoint] = (
            self._graph_service.source_nodes_of_type(
                node=target_time_point,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.PRECEDES,
            )
        )
        if existing_previous_points:
            raise ValueError(
                f"MeasureTimePoint {target_time_point} "
                f"already has a previous time point"
            )

        if source_time_point.position >= target_time_point.position:
            raise ValueError(
                "The source time point must be earlier than the target time point."
            )

        self._graph_service.connect(
            source=source_time_point,
            target=target_time_point,
            relation=EdgeRelation.PRECEDES,
        )
