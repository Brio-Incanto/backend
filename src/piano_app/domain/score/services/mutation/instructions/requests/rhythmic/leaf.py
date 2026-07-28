from dataclasses import dataclass

from piano_app.domain.score.models.notation import RhythmicSize
from piano_app.domain.score.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)
from piano_app.domain.score.services.mutation.instructions.refs import Bound, ResultRef
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    MutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLeafRhythmicContainerRequest(MutationRequest):
    """Create a leaf for a voice at a position. The leaf's anchor is resolved
    by the leaf analyzer (find-or-create), so callers pass the slot, not the
    anchor."""

    voice: Voice
    measure: Measure
    position: MeasurePosition
    written_size: RhythmicSize
    occupied_size: RhythmicSize
    parent: Bound[RhythmicContainerParent] | None = None

    out: ResultRef[LeafRhythmicContainer]

    @property
    def produced_ref(self) -> ResultRef[LeafRhythmicContainer]:
        return self.out
