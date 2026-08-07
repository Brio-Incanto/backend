from dataclasses import dataclass

from piano_app.domain.score.document.models.material import Note
from piano_app.domain.score.document.models.relations import Tie
from piano_app.domain.score.document.services.mutation.instructions import Bound
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTieAction(CreateMutationAction[Tie]):
    """Creates a tie between two notes."""

    # TODO consider making Note only
    start_note: Bound[Note]
    end_note: Bound[Note]
