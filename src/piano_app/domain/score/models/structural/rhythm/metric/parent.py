from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from .base import RhythmicContainer


class RhythmicContainerParent(Protocol):
    _children: list[RhythmicContainer]

    @property
    def children(self) -> Sequence[RhythmicContainer]: ...

    def add_child(
        self,
        *,
        child: RhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None: ...

    def remove_child(
        self,
        *,
        child: RhythmicContainer,
        sink: MutationSink = DIRECT_SINK,
    ) -> None: ...
