from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import HairpinType
from piano_app.domain.shared.abstract import abstract

from .base import SpanContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor, Voice


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class VoicesSpanContext(SpanContext):
    """A span context scoped to a set of voices."""

    voices: list[Voice]

    def __post_init__(self) -> None:
        super().__post_init__()

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
class Hairpin(VoicesSpanContext):
    hairpin_type: HairpinType

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        end: TemporalAnchor,
        voices: list[Voice],
        hairpin_type: HairpinType,
        sink: MutationSink = DIRECT_SINK,
    ) -> Hairpin:
        hairpin: Hairpin = cls(
            start=start,
            end=end,
            voices=voices,
            hairpin_type=hairpin_type,
        )
        hairpin.attach(sink=sink)
        return hairpin

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        end: TemporalAnchor,
        voices: list[Voice],
        hairpin_type: HairpinType,
        sink: MutationSink = DIRECT_SINK,
    ) -> Hairpin:
        hairpin: Hairpin = cls(
            id=id,
            start=start,
            end=end,
            voices=voices,
            hairpin_type=hairpin_type,
        )
        hairpin.attach(sink=sink)
        return hairpin


@dataclass(slots=True, kw_only=True, eq=False)
class Slur(VoicesSpanContext):
    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        end: TemporalAnchor,
        voices: list[Voice],
        sink: MutationSink = DIRECT_SINK,
    ) -> Slur:
        slur: Slur = cls(start=start, end=end, voices=voices)
        slur.attach(sink=sink)
        return slur

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        end: TemporalAnchor,
        voices: list[Voice],
        sink: MutationSink = DIRECT_SINK,
    ) -> Slur:
        slur: Slur = cls(id=id, start=start, end=end, voices=voices)
        slur.attach(sink=sink)
        return slur
