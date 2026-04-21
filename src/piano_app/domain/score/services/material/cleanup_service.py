from piano_app.domain.score.models.graph import EdgeRelation
from piano_app.domain.score.models.graph.nodes.material import (
    Carrier,
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.services.graph_service import GraphService


class MaterialCleanupService:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    # -------------------------------------------------------------------------
    # Raw removals
    # -------------------------------------------------------------------------

    def _remove_note_raw(
        self,
        note: Note,
    ) -> None:
        self._graph_service.remove_edges_of(note)
        self._graph_service.remove_node(note)

    def _remove_rest_raw(
        self,
        rest: Rest,
    ) -> None:
        self._graph_service.remove_edges_of(rest)
        self._graph_service.remove_node(rest)

    def _remove_sound_carrier_raw(
        self,
        carrier: SoundCarrier,
    ) -> None:
        self._graph_service.remove_edges_of(carrier)
        self._graph_service.remove_node(carrier)

    def _remove_rest_carrier_raw(
        self,
        carrier: RestCarrier,
    ) -> None:
        self._graph_service.remove_edges_of(carrier)
        self._graph_service.remove_node(carrier)

    # -------------------------------------------------------------------------
    # Internal queries
    # -------------------------------------------------------------------------

    def _notes_of_sound_carrier(
        self,
        carrier: SoundCarrier,
    ) -> list[Note]:
        return self._graph_service.target_nodes_of_type(
            carrier,
            node_type=Note,
            relation=EdgeRelation.CONTAINS,
        )

    def _rest_of_rest_carrier(
        self,
        carrier: RestCarrier,
    ) -> Rest:
        rests: list[Rest] = self._graph_service.target_nodes_of_type(
            carrier,
            node_type=Rest,
            relation=EdgeRelation.CONTAINS,
        )
        return rests[0]

    def _sound_carrier_of_note(
        self,
        note: Note,
    ) -> SoundCarrier:
        carriers: list[SoundCarrier] = self._graph_service.source_nodes_of_type(
            note,
            node_type=SoundCarrier,
            relation=EdgeRelation.CONTAINS,
        )
        return carriers[0]

    def _rest_carrier_of_rest(
        self,
        rest: Rest,
    ) -> RestCarrier:
        carriers: list[RestCarrier] = self._graph_service.source_nodes_of_type(
            rest,
            node_type=RestCarrier,
            relation=EdgeRelation.CONTAINS,
        )
        return carriers[0]

    # -------------------------------------------------------------------------
    # Cleanup rules
    # -------------------------------------------------------------------------

    def remove_note(
        self,
        note: Note,
    ) -> None:
        carrier: SoundCarrier = self._sound_carrier_of_note(note)

        self._remove_note_raw(note)

        remaining_notes: list[Note] = self._notes_of_sound_carrier(carrier)
        if not remaining_notes:
            self._remove_sound_carrier_raw(carrier)

    def remove_rest(
        self,
        rest: Rest,
    ) -> None:
        carrier: RestCarrier = self._rest_carrier_of_rest(rest)

        self._remove_rest_raw(rest)
        self._remove_rest_carrier_raw(carrier)

    def remove_sound_carrier(
        self,
        carrier: SoundCarrier,
    ) -> None:
        notes: list[Note] = self._notes_of_sound_carrier(carrier)

        for note in notes:
            self._remove_note_raw(note)

        self._remove_sound_carrier_raw(carrier)

    def remove_rest_carrier(
        self,
        carrier: RestCarrier,
    ) -> None:
        rest: Rest = self._rest_of_rest_carrier(carrier)

        self._remove_rest_raw(rest)
        self._remove_rest_carrier_raw(carrier)

    def remove_carrier(
        self,
        carrier: Carrier,
    ) -> None:
        if isinstance(carrier, SoundCarrier):
            self.remove_sound_carrier(carrier)
        elif isinstance(carrier, RestCarrier):
            self.remove_rest_carrier(carrier)
