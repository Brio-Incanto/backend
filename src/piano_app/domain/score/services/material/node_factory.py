from piano_app.domain.score.models.graph import Node
from piano_app.domain.score.models.graph.nodes.material import (
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.models.graph.notation import (
    Accidental,
    Articulation,
    Fingering,
    RhythmicValue,
)
from piano_app.domain.score.services.graph_service import GraphService


class MaterialNodeFactory:
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

    def _update[T: Node](
        self,
        node: T,
        **kwargs: object | None,
    ) -> T:
        changes: dict[str, object] = {
            key: value for key, value in kwargs.items() if value is not None
        }

        return self._graph_service.update_node(
            old_node=node,
            **changes,
        )

    def create_note(
        self,
        *,
        staff_step: int,
        accidental: Accidental = Accidental.NONE,
        fingering: Fingering = Fingering.NONE,
    ) -> Note:
        return self._create(
            Note,
            staff_step=staff_step,
            accidental=accidental,
            fingering=fingering,
        )

    def update_note(
        self,
        note: Note,
        *,
        staff_step: int | None = None,
        accidental: Accidental | None = None,
        fingering: Fingering | None = None,
    ) -> Note:
        return self._update(
            note,
            staff_step=staff_step,
            accidental=accidental,
            fingering=fingering,
        )

    def create_sound_carrier(
        self,
        *,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
        articulation: Articulation = Articulation.NONE,
    ) -> SoundCarrier:
        return self._create(
            SoundCarrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
            articulation=articulation,
        )

    def update_sound_carrier(
        self,
        carrier: SoundCarrier,
        *,
        rhythmic_value: RhythmicValue | None = None,
        dot_count: int | None = None,
        articulation: Articulation | None = None,
    ) -> SoundCarrier:
        return self._update(
            carrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
            articulation=articulation,
        )

    def create_rest(
        self,
        *,
        staff_step: int,
    ) -> Rest:
        return self._create(
            Rest,
            staff_step=staff_step,
        )

    def update_rest(
        self,
        rest: Rest,
        *,
        staff_step: int | None = None,
    ) -> Rest:
        return self._update(
            rest,
            staff_step=staff_step,
        )

    def create_rest_carrier(
        self,
        *,
        rhythmic_value: RhythmicValue,
        dot_count: int = 0,
    ) -> RestCarrier:
        return self._create(
            RestCarrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )

    def update_rest_carrier(
        self,
        carrier: RestCarrier,
        *,
        rhythmic_value: RhythmicValue | None = None,
        dot_count: int | None = None,
    ) -> RestCarrier:
        return self._update(
            carrier,
            rhythmic_value=rhythmic_value,
            dot_count=dot_count,
        )
