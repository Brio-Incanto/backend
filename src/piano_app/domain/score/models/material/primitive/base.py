from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.base import ScoreEntity
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.shared.abstract import abstract

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural import Staff


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class MusicalItem(ScoreEntity):
    """
    Staff step index:
    0 is the first line,
    1 is the first gap above it,
    -1 is the gap below the first line.
    """

    staff_step: int
    _staff: Staff

    @property
    def staff(self) -> Staff:
        return self._staff

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._staff.add_musical_item(musical_item=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._staff.remove_musical_item(musical_item=self, sink=sink)
