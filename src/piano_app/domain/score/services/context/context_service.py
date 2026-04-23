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
from piano_app.domain.score.models.graph.notation import (
    Accidental,
    Clef,
    DynamicMarking,
    NoteName,
    RhythmicValue,
    TempoMarking,
)
from piano_app.domain.score.services.cleanup import CleanupEngine, DeleteRequest

from .graph_binder import ContextGraphBinder
from .node_factory import ContextNodeFactory


class ContextService:
    def __init__(
        self,
        *,
        node_factory: ContextNodeFactory,
        graph_binder: ContextGraphBinder,
        cleanup_engine: CleanupEngine,
    ) -> None:
        self._node_factory: ContextNodeFactory = node_factory
        self._graph_binder: ContextGraphBinder = graph_binder
        self._cleanup_engine: CleanupEngine = cleanup_engine

    def insert_clef_change(
        self,
        *,
        clef: Clef,
        octave_transposition: int = 0,
        staff: Staff,
        time_point: MeasureTimePoint,
    ) -> ClefChange:
        clef_change: ClefChange = self._node_factory.create_clef_change(
            clef=clef,
            octave_transposition=octave_transposition,
        )

        try:
            self._graph_binder.attach_clef_change_to_staff(
                clef_change=clef_change,
                staff=staff,
            )
            self._graph_binder.attach_clef_change_to_time_point(
                clef_change=clef_change,
                time_point=time_point,
            )
        except Exception:
            self._cleanup_engine.delete(
                DeleteRequest(node=clef_change),
            )
            raise

        return clef_change

    def insert_dynamic_change(
        self,
        *,
        dynamic: DynamicMarking,
        voices: list[Voice],
        time_point: MeasureTimePoint,
    ) -> DynamicChange:
        dynamic_change: DynamicChange = self._node_factory.create_dynamic_change(
            dynamic=dynamic,
        )

        try:
            for voice in voices:
                self._graph_binder.attach_dynamic_change_to_voice(
                    dynamic_change=dynamic_change,
                    voice=voice,
                )

            self._graph_binder.attach_dynamic_change_to_time_point(
                dynamic_change=dynamic_change,
                time_point=time_point,
            )
        except Exception:
            self._cleanup_engine.delete(
                DeleteRequest(node=dynamic_change),
            )
            raise

        return dynamic_change

    def insert_key_signature_change(
        self,
        *,
        accidental: Accidental,
        notes: tuple[NoteName, ...],
        staff: Staff,
        time_point: MeasureTimePoint,
    ) -> KeySignatureChange:
        key_signature_change: KeySignatureChange = (
            self._node_factory.create_key_signature_change(
                accidental=accidental,
                notes=notes,
            )
        )

        try:
            self._graph_binder.attach_key_signature_change_to_staff(
                key_signature_change=key_signature_change,
                staff=staff,
            )
            self._graph_binder.attach_key_signature_change_to_time_point(
                key_signature_change=key_signature_change,
                time_point=time_point,
            )
        except Exception:
            self._cleanup_engine.delete(
                DeleteRequest(node=key_signature_change),
            )
            raise

        return key_signature_change

    def insert_tempo_change(
        self,
        *,
        bpm: int,
        marking: TempoMarking,
        time_point: MeasureTimePoint,
    ) -> TempoChange:
        tempo_change: TempoChange = self._node_factory.create_tempo_change(
            bpm=bpm,
            marking=marking,
        )

        try:
            self._graph_binder.attach_tempo_change_to_time_point(
                tempo_change=tempo_change,
                time_point=time_point,
            )
        except Exception:
            self._cleanup_engine.delete(
                DeleteRequest(node=tempo_change),
            )
            raise

        return tempo_change

    def insert_time_signature_change(
        self,
        *,
        beats_per_measure: int,
        beat_unit: RhythmicValue,
        measure: Measure,
    ) -> TimeSignatureChange:
        time_signature_change: TimeSignatureChange = (
            self._node_factory.create_time_signature_change(
                beats_per_measure=beats_per_measure,
                beat_unit=beat_unit,
            )
        )

        try:
            self._graph_binder.attach_time_signature_change_to_measure(
                time_signature_change=time_signature_change,
                measure=measure,
            )
        except Exception:
            self._cleanup_engine.delete(
                DeleteRequest(node=time_signature_change),
            )
            raise

        return time_signature_change

    def delete_clef_change(
        self,
        clef_change: ClefChange,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=clef_change),
        )

    def delete_dynamic_change(
        self,
        dynamic_change: DynamicChange,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=dynamic_change),
        )

    def delete_key_signature_change(
        self,
        key_signature_change: KeySignatureChange,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=key_signature_change),
        )

    def delete_tempo_change(
        self,
        tempo_change: TempoChange,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=tempo_change),
        )

    def delete_time_signature_change(
        self,
        time_signature_change: TimeSignatureChange,
    ) -> None:
        self._cleanup_engine.delete(
            DeleteRequest(node=time_signature_change),
        )
