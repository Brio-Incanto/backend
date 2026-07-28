from dataclasses import dataclass

from piano_app.domain.score.models.material import Note
from piano_app.domain.score.models.relations.start_end import Tie
from piano_app.domain.score.services.mutation.instructions import Bound
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTieRequest(CreateMutationRequest[Tie]):
    """A request to create a tie between two notes."""

    start_note: Bound[Note]
    end_note: Bound[Note]
