from piano_app.domain.score.models.graph import EdgeRelation, Node
from piano_app.domain.score.models.graph.nodes.material import (
    Carrier,
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.models.graph.nodes.structural import Staff, TimePoint, Voice
from piano_app.domain.score.models.graph.notation import (
    Accidental,
    Articulation,
    Fingering,
    RhythmicValue,
)
from piano_app.domain.score.services.graph_service import GraphService


class MaterialService:
    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service: GraphService = graph_service

    @staticmethod
    def _build_update_kwargs(**kwargs: object | None) -> dict[str, object]:
        return {key: value for key, value in kwargs.items() if value is not None}

    # -------------------------------------------------------------------------
    # Node creation / update
    # -------------------------------------------------------------------------

    def _create_note(
        self,
        *,
        staff_step: int,
        accidental: Accidental = Accidental.NONE,
        fingering: Fingering = Fingering.NONE,
    ) -> Note:
        return self._graph_service.create_node(
            node_type=Note,
            staff_step=staff_step,
            accidental=accidental,
            fingering=fingering,
        )

    def _update_note(
        self,
        note: Note,
        *,
        staff_step: int | None = None,
        accidental: Accidental | None = None,
        fingering: Fingering | None = None,
    ) -> Note:
        kwargs: dict[str, object] = self._build_update_kwargs(
            staff_step=staff_step,
            accidental=accidental,
            fingering=fingering,
        )

        return self._graph_service.update_node(
            old_node=note,
            **kwargs,
        )

    def _create_sound_carrier(
        self,
        *,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
        articulation: Articulation = Articulation.NONE,
    ) -> SoundCarrier:
        return self._graph_service.create_node(
            node_type=SoundCarrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
            articulation=articulation,
        )

    def _update_sound_carrier(
        self,
        carrier: SoundCarrier,
        *,
        rhythmic_value: RhythmicValue | None = None,
        dot_count: int | None = None,
        articulation: Articulation | None = None,
    ) -> SoundCarrier:
        kwargs: dict[str, object] = self._build_update_kwargs(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
            articulation=articulation,
        )

        return self._graph_service.update_node(
            old_node=carrier,
            **kwargs,
        )

    def _create_rest(
        self,
        *,
        staff_step: int,
    ) -> Rest:
        return self._graph_service.create_node(
            node_type=Rest,
            staff_step=staff_step,
        )

    def _update_rest(
        self,
        rest: Rest,
        *,
        staff_step: int | None = None,
    ) -> Rest:
        kwargs: dict[str, object] = self._build_update_kwargs(
            staff_step=staff_step,
        )

        return self._graph_service.update_node(
            old_node=rest,
            **kwargs,
        )

    def _create_rest_carrier(
        self,
        *,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
    ) -> RestCarrier:
        return self._graph_service.create_node(
            node_type=RestCarrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )

    def _update_rest_carrier(
        self,
        carrier: RestCarrier,
        *,
        rhythmic_value: RhythmicValue | None = None,
        dot_count: int | None = None,
    ) -> RestCarrier:
        kwargs: dict[str, object] = self._build_update_kwargs(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )

        return self._graph_service.update_node(
            old_node=carrier,
            **kwargs,
        )

    # -------------------------------------------------------------------------
    # Internal graph attachments
    # -------------------------------------------------------------------------

    def _add_note_to_sound_carrier(
        self,
        *,
        carrier: SoundCarrier,
        note: Note,
    ) -> None:
        self._graph_service.connect(
            source=carrier,
            target=note,
            relation=EdgeRelation.CONTAINS,
        )

    def _add_rest_to_rest_carrier(
        self,
        *,
        carrier: RestCarrier,
        rest: Rest,
    ) -> None:
        self._graph_service.connect(
            source=carrier,
            target=rest,
            relation=EdgeRelation.CONTAINS,
        )

    def _attach_note_to_staff(
        self,
        *,
        note: Note,
        staff: Staff,
    ) -> None:
        self._graph_service.connect(
            source=note,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def _attach_rest_to_staff(
        self,
        *,
        rest: Rest,
        staff: Staff,
    ) -> None:
        self._graph_service.connect(
            source=rest,
            target=staff,
            relation=EdgeRelation.BELONGS_TO,
        )

    def _attach_carrier_to_voice(
        self,
        *,
        carrier: Carrier,
        voice: Voice,
    ) -> None:
        self._graph_service.connect(
            source=carrier,
            target=voice,
            relation=EdgeRelation.BELONGS_TO,
        )

    def _attach_carrier_to_time_point(
        self,
        *,
        carrier: Carrier,
        time_point: TimePoint,
    ) -> None:
        self._graph_service.connect(
            source=carrier,
            target=time_point,
            relation=EdgeRelation.STARTS_AT,
        )

    # -------------------------------------------------------------------------
    # Internal removals
    # -------------------------------------------------------------------------

    def _remove_note(
        self,
        note: Note,
    ) -> None:
        self._graph_service.remove_edges_of(note)
        self._graph_service.remove_node(note)

    def _remove_rest(
        self,
        rest: Rest,
    ) -> None:
        self._graph_service.remove_edges_of(rest)
        self._graph_service.remove_node(rest)

    def _remove_sound_carrier(
        self,
        carrier: SoundCarrier,
    ) -> None:
        contained_nodes: list[Node] = self._graph_service.targets(
            carrier,
            relation=EdgeRelation.CONTAINS,
        )

        for node in contained_nodes:
            if isinstance(node, Note):
                self._remove_note(node)

        self._graph_service.remove_edges_of(carrier)
        self._graph_service.remove_node(carrier)

    def _remove_rest_carrier(
        self,
        carrier: RestCarrier,
    ) -> None:
        contained_nodes: list[Node] = self._graph_service.targets(
            carrier,
            relation=EdgeRelation.CONTAINS,
        )

        for node in contained_nodes:
            if isinstance(node, Rest):
                self._remove_rest(node)

        self._graph_service.remove_edges_of(carrier)
        self._graph_service.remove_node(carrier)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def insert_note(
        self,
        *,
        voice: Voice,
        staff: Staff,
        time_point: TimePoint,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
        staff_step: int,
    ) -> tuple[SoundCarrier, Note]:
        carrier: SoundCarrier = self._create_sound_carrier(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )
        note: Note = self._create_note(
            staff_step=staff_step,
        )

        self._add_note_to_sound_carrier(carrier=carrier, note=note)
        self._attach_note_to_staff(note=note, staff=staff)
        self._attach_carrier_to_voice(carrier=carrier, voice=voice)
        self._attach_carrier_to_time_point(carrier=carrier, time_point=time_point)

        return carrier, note

    def add_note_to_sound_carrier(
        self,
        *,
        carrier: SoundCarrier,
        staff: Staff,
        staff_step: int,
    ) -> Note:
        note: Note = self._create_note(
            staff_step=staff_step,
        )

        self._add_note_to_sound_carrier(carrier=carrier, note=note)
        self._attach_note_to_staff(note=note, staff=staff)

        return note

    def insert_rest(
        self,
        *,
        voice: Voice,
        staff: Staff,
        time_point: TimePoint,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
        staff_step: int,
    ) -> tuple[RestCarrier, Rest]:
        carrier: RestCarrier = self._create_rest_carrier(
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )
        rest: Rest = self._create_rest(
            staff_step=staff_step,
        )

        self._add_rest_to_rest_carrier(carrier=carrier, rest=rest)
        self._attach_rest_to_staff(rest=rest, staff=staff)
        self._attach_carrier_to_voice(carrier=carrier, voice=voice)
        self._attach_carrier_to_time_point(carrier=carrier, time_point=time_point)

        return carrier, rest

    def remove_carrier(self, carrier: Carrier) -> None:
        if isinstance(carrier, SoundCarrier):
            self._remove_sound_carrier(carrier)
        elif isinstance(carrier, RestCarrier):
            self._remove_rest_carrier(carrier)
