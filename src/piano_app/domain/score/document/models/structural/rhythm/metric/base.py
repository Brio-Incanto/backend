from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.base import ScoreEntity
from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.document.models.notation import RhythmicSize
from piano_app.domain.shared.abstract import abstract

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.structural import TemporalAnchor

    from .parent import RhythmicContainerParent


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class RhythmicContainer(ScoreEntity):
    written_size: RhythmicSize  # capacity of this container
    occupied_size: RhythmicSize  # actual size of this container

    _parent: RhythmicContainerParent

    @property
    def parent(self) -> RhythmicContainerParent:
        return self._parent

    @property
    def start_anchor(self) -> TemporalAnchor:
        """The anchor where this container begins — its earliest."""
        raise NotImplementedError

    def precedes(self, other: RhythmicContainer) -> bool:
        return self.start_anchor.precedes(other.start_anchor)

    def attach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._parent.add_child(child=self, sink=sink)

    def detach(
        self,
        *,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        self._parent.remove_child(child=self, sink=sink)
