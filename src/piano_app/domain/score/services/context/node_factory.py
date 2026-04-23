from piano_app.domain.score.models.graph import Node
from piano_app.domain.score.models.graph.nodes.context import (
    ClefChange,
    DynamicChange,
    KeySignatureChange,
    TempoChange,
    TimeSignatureChange,
)
from piano_app.domain.score.models.graph.notation import (
    Accidental,
    Clef,
    DynamicMarking,
    NoteName,
    RhythmicValue,
    TempoMarking,
)
from piano_app.domain.score.services.graph_service import GraphService


class ContextNodeFactory:
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

    def create_clef_change(
        self,
        *,
        clef: Clef,
        octave_transposition: int = 0,
    ) -> ClefChange:
        return self._create(
            ClefChange,
            clef=clef,
            octave_transposition=octave_transposition,
        )

    def update_clef_change(
        self,
        clef_change: ClefChange,
        *,
        clef: Clef | None = None,
        octave_transposition: int | None = None,
    ) -> ClefChange:
        return self._update(
            clef_change,
            clef=clef,
            octave_transposition=octave_transposition,
        )

    def create_dynamic_change(
        self,
        *,
        dynamic: DynamicMarking,
    ) -> DynamicChange:
        return self._create(
            DynamicChange,
            dynamic=dynamic,
        )

    def update_dynamic_change(
        self,
        dynamic_change: DynamicChange,
        *,
        dynamic: DynamicMarking | None = None,
    ) -> DynamicChange:
        return self._update(
            dynamic_change,
            dynamic=dynamic,
        )

    def create_key_signature_change(
        self,
        *,
        accidental: Accidental = Accidental.NONE,
        notes: tuple[NoteName, ...] = (),
    ) -> KeySignatureChange:
        return self._create(
            KeySignatureChange,
            accidental=accidental,
            notes=notes,
        )

    def update_key_signature_change(
        self,
        key_signature_change: KeySignatureChange,
        *,
        accidental: Accidental | None = None,
        notes: tuple[NoteName, ...] | None = None,
    ) -> KeySignatureChange:
        return self._update(
            key_signature_change,
            accidental=accidental,
            notes=notes,
        )

    def create_tempo_change(
        self,
        *,
        bpm: int,
        marking: TempoMarking,
    ) -> TempoChange:
        return self._create(
            TempoChange,
            bpm=bpm,
            marking=marking,
        )

    def update_tempo_change(
        self,
        tempo_change: TempoChange,
        *,
        bpm: int | None = None,
        marking: TempoMarking | None = None,
    ) -> TempoChange:
        return self._update(
            tempo_change,
            bpm=bpm,
            marking=marking,
        )

    def create_time_signature_change(
        self,
        *,
        beats_per_measure: int,
        beat_unit: RhythmicValue,
    ) -> TimeSignatureChange:
        return self._create(
            TimeSignatureChange,
            beats_per_measure=beats_per_measure,
            beat_unit=beat_unit,
        )

    def update_time_signature_change(
        self,
        time_signature_change: TimeSignatureChange,
        *,
        beats_per_measure: int | None = None,
        beat_unit: RhythmicValue | None = None,
    ) -> TimeSignatureChange:
        return self._update(
            time_signature_change,
            beats_per_measure=beats_per_measure,
            beat_unit=beat_unit,
        )
