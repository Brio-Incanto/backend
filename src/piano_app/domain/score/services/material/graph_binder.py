from piano_app.domain.score.models.graph import EdgeRelation
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
from piano_app.domain.score.services.graph_service import GraphService


class MaterialGraphBinder:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    def attach_note_to_sound_carrier(
        self,
        *,
        carrier: SoundCarrier,
        note: Note,
    ) -> None:
        note_carriers: list[SoundCarrier] = self._graph_service.source_nodes_of_type(
            node=note,
            node_type=SoundCarrier,
            relation=EdgeRelation.CONTAINS,
        )

        if note_carriers:
            raise ValueError(f"Note {note} already belongs to a SoundCarrier")

        self._graph_service.connect(
            source=carrier,
            target=note,
            relation=EdgeRelation.CONTAINS,
        )

    def attach_rest_to_rest_carrier(
        self,
        *,
        carrier: RestCarrier,
        rest: Rest,
    ) -> None:
        rest_carriers: list[RestCarrier] = self._graph_service.source_nodes_of_type(
            node=rest,
            node_type=RestCarrier,
            relation=EdgeRelation.CONTAINS,
        )

        if rest_carriers:
            raise ValueError(f"Rest {rest} already belongs to a RestCarrier")

        contained_rests: list[Rest] = self._graph_service.target_nodes_of_type(
            node=carrier,
            node_type=Rest,
            relation=EdgeRelation.CONTAINS,
        )
        if contained_rests:
            raise ValueError(f"RestCarrier {carrier} already contains a Rest")

        self._graph_service.connect(
            source=carrier,
            target=rest,
            relation=EdgeRelation.CONTAINS,
        )

    def attach_note_to_staff(
        self,
        *,
        note: Note,
        staff: Staff,
    ) -> None:
        existing_staffs: list[Staff] = self._graph_service.target_nodes_of_type(
            node=note,
            node_type=Staff,
            relation=EdgeRelation.BELONGS_TO,
        )

        if existing_staffs:
            raise ValueError(f"Note {note} already belongs to a Staff")

        self._graph_service.connect(
            source=note,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_rest_to_staff(
        self,
        *,
        rest: Rest,
        staff: Staff,
    ) -> None:
        existing_staffs: list[Staff] = self._graph_service.target_nodes_of_type(
            node=rest,
            node_type=Staff,
            relation=EdgeRelation.BELONGS_TO,
        )

        if existing_staffs:
            raise ValueError(f"Rest {rest} already belongs to a Staff")

        self._graph_service.connect(
            source=rest,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_carrier_to_voice(
        self,
        *,
        carrier: Carrier,
        voice: Voice,
    ) -> None:
        existing_voices: list[Voice] = self._graph_service.target_nodes_of_type(
            node=carrier,
            node_type=Voice,
            relation=EdgeRelation.BELONGS_TO,
        )

        if existing_voices:
            raise ValueError(f"Carrier {carrier} already belongs to a Voice")

        self._graph_service.connect(
            source=carrier,
            target=voice,
            relation=EdgeRelation.BELONGS_TO,
        )

    def attach_carrier_to_time_point(
        self,
        *,
        carrier: Carrier,
        time_point: MeasureTimePoint,
    ) -> None:
        existing_time_points: list[MeasureTimePoint] = (
            self._graph_service.target_nodes_of_type(
                node=carrier,
                node_type=MeasureTimePoint,
                relation=EdgeRelation.STARTS_AT,
            )
        )

        if existing_time_points:
            raise ValueError(f"Carrier {carrier} already starts at a MeasureTimePoint")

        self._graph_service.connect(
            source=carrier,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )
