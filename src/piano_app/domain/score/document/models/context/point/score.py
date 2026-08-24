from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import TempoMarking
from piano_app.domain.shared.abstract import abstract

from .base import PointContext

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class ScorePointContext(PointContext):
    """A point context scoped to the whole score."""


@dataclass(slots=True, kw_only=True, eq=False)
class TempoChange(ScorePointContext):
    """A tempo assertion — a metronome mark, a word marking, or both.

    Both are optional individually (a score may show only "Allegro" with no BPM, or
    only "♩ = 120" with no word marking) but not both absent — that would assert
    nothing.
    """

    bpm: int | None = None
    marking: TempoMarking | None = None

    def __post_init__(self) -> None:
        if self.bpm is not None and self.bpm < 1:
            raise ValueError("Tempo must be at least 1 BPM.")

        if self.bpm is None and self.marking is None:
            raise ValueError("Tempo change must give a BPM, a marking, or both.")

    @classmethod
    def create(
        cls,
        *,
        start: TemporalAnchor,
        bpm: int | None = None,
        marking: TempoMarking | None = None,
        sink: MutationSink = DIRECT_SINK,
    ) -> TempoChange:
        tempo_change: TempoChange = cls(start=start, bpm=bpm, marking=marking)
        tempo_change.attach(sink=sink)
        return tempo_change

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        start: TemporalAnchor,
        bpm: int | None = None,
        marking: TempoMarking | None = None,
        sink: MutationSink = DIRECT_SINK,
    ) -> TempoChange:
        tempo_change: TempoChange = cls(id=id, start=start, bpm=bpm, marking=marking)
        tempo_change.attach(sink=sink)
        return tempo_change
