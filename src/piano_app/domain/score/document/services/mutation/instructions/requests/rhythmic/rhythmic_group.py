from dataclasses import dataclass

from piano_app.domain.score.document.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.document.services.mutation.instructions.requests.base import (
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRhythmicGroupRequest(DeleteMutationRequest[GroupRhythmicContainer]):
    """A request to delete a rhythmic group container."""
