from piano_app.domain.score.models.graph import Node
from piano_app.domain.score.models.graph.nodes.structural import (
    Measure,
    MeasurePosition,
    MeasureTimePoint,
    Staff,
    Voice,
)
from piano_app.domain.score.services.graph_service import GraphService


class StructuralNodeFactory:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    def _create[T: Node](
        self,
        node_type: type[T],
        **kwargs: object,
    ) -> T:
        return self._graph_service.create_node(
            node_type=node_type,
            **kwargs,
        )

    def create_measure(self) -> Measure:
        return self._create(Measure)

    def create_staff(self) -> Staff:
        return self._create(Staff)

    def create_voice(self) -> Voice:
        return self._create(Voice)

    def create_time_point(
        self,
        *,
        numerator: int,
        denominator: int,
    ) -> MeasureTimePoint:
        position: MeasurePosition = MeasurePosition(
            numerator=numerator,
            denominator=denominator,
        )

        return self._create(
            MeasureTimePoint,
            position=position,
        )
