from dataclasses import dataclass

from piano_app.domain.score.models.material import Note
from piano_app.domain.score.models.relations.start_end import Tie
from piano_app.domain.score.services.mutation.instructions import Bound
from piano_app.domain.score.services.mutation.instructions.actions.base import CreateMutationAction


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTieAction(CreateMutationAction[Tie]):
    """Creates a tie between two notes."""

    start_note: Bound[Note]
    end_note: Bound[Note]
