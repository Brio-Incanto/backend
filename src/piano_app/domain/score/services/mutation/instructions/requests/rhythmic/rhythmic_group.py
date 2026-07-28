from dataclasses import dataclass

from piano_app.domain.score.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRhythmicGroupRequest(DeleteMutationRequest[GroupRhythmicContainer]):
    """A request to delete a rhythmic group container."""
