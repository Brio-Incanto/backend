from dataclasses import dataclass

from piano_app.domain.score.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.services.mutation.instructions.actions.base import DeleteMutationAction


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRhythmicGroupAction(DeleteMutationAction[GroupRhythmicContainer]):
    """Deletes a rhythmic group container."""
