from dataclasses import dataclass

from piano_app.domain.score.models.notation import RhythmicSize
from piano_app.domain.score.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLeafRequest(CreateMutationRequest[LeafRhythmicContainer]):
    """A request to create a leaf rhythmic container for a voice at a measure position."""

    voice: Voice
    measure: Measure
    position: MeasurePosition
    size: RhythmicSize


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteLeafRequest(DeleteMutationRequest[LeafRhythmicContainer]):
    """A request to delete a leaf rhythmic container."""
