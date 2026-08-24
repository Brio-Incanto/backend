from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import DynamicMarking
from piano_app.domain.shared.abstract import abstract

from .base import PointContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor, Voice


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class VoicesPointContext(PointContext):
    """A point context scoped to a set of voices."""

    voices: list[Voice]

    def __post_init__(self) -> None:
        if not self.voices:
            raise ValueError("Voices scope must contain at least one voice.")

        if len(self.voices) != len(set(map(id, self.voices))):
            raise ValueError("Voices scope must not repeat a voice.")

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        for voice in self.voices:
            voice.add_context(context=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        for voice in self.voices:
            voice.remove_context(context=self, sink=sink)
        super().detach(sink=sink)


@dataclass(slots=True, kw_only=True, eq=False)
class DynamicChange(VoicesPointContext):
    dynamic: DynamicMarking

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        voices: list[Voice],
        dynamic: DynamicMarking,
        sink: MutationSink = DIRECT_SINK,
    ) -> DynamicChange:
        dynamic_change: DynamicChange = cls(start=start, voices=voices, dynamic=dynamic)
        dynamic_change.attach(sink=sink)
        return dynamic_change

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        voices: list[Voice],
        dynamic: DynamicMarking,
        sink: MutationSink = DIRECT_SINK,
    ) -> DynamicChange:
        dynamic_change: DynamicChange = cls(
            id=id,
            start=start,
            voices=voices,
            dynamic=dynamic,
        )
        dynamic_change.attach(sink=sink)
        return dynamic_change
