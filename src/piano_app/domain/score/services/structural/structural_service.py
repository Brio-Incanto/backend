from piano_app.domain.score.models.graph.nodes.structural import (
    Measure,
    MeasureTimePoint,
    Staff,
    Voice,
)
from piano_app.domain.score.services.cleanup import CleanupEngine
from piano_app.domain.score.services.cleanup.delete_request import DeleteRequest

from .graph_binder import StructuralGraphBinder
from .node_factory import StructuralNodeFactory


class StructuralService:
    def __init__(
        self,
        *,
        node_factory: StructuralNodeFactory,
        graph_binder: StructuralGraphBinder,
        cleanup_engine: CleanupEngine,
    ) -> None:
        self._node_factory: StructuralNodeFactory = node_factory
        self._graph_binder: StructuralGraphBinder = graph_binder
        self._cleanup_engine: CleanupEngine = cleanup_engine

    def create_root_measure(
        self,
    ) -> Measure:
        return self._node_factory.create_measure()

    def add_next_measure(
        self,
        *,
        prev: Measure,
    ) -> Measure:
        measure: Measure = self._node_factory.create_measure()

        self._graph_binder.attach_next_measure(
            source_measure=prev,
            target_measure=measure,
        )

        return measure

    def create_staff(
        self,
    ) -> Staff:
        return self._node_factory.create_staff()

    def create_voice(
        self,
    ) -> Voice:
        return self._node_factory.create_voice()

    def add_root_time_point(
        self,
        *,
        numerator: int,
        denominator: int,
        measure: Measure,
    ) -> MeasureTimePoint:
        time_point: MeasureTimePoint = self._node_factory.create_time_point(
            numerator=numerator,
            denominator=denominator,
        )

        self._graph_binder.attach_time_point_to_measure(
            measure=measure,
            time_point=time_point,
        )

        return time_point

    def add_next_time_point(
        self,
        *,
        numerator: int,
        denominator: int,
        prev: MeasureTimePoint,
        measure: Measure,
    ) -> MeasureTimePoint:
        time_point: MeasureTimePoint = self._node_factory.create_time_point(
            numerator=numerator,
            denominator=denominator,
        )

        self._graph_binder.attach_time_point_to_measure(
            measure=measure,
            time_point=time_point,
        )
        self._graph_binder.attach_next_time_point(
            source_time_point=prev,
            target_time_point=time_point,
        )

        return time_point

    def delete_measure(
        self,
        measure: Measure,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=measure),
        )

    def delete_time_point(
        self,
        time_point: MeasureTimePoint,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=time_point),
        )

    def delete_voice(
        self,
        voice: Voice,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=voice),
        )

    def delete_staff(
        self,
        staff: Staff,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=staff),
        )
