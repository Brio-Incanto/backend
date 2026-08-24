from dataclasses import dataclass

from piano_app.domain.score.document.models.context import ClefChange
from piano_app.domain.score.document.models.notation import Clef
from piano_app.domain.score.document.models.structural import Staff, TemporalAnchor
from piano_app.domain.score.document.services.mutation.instructions import Bound
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateClefChangeAction(CreateMutationAction[ClefChange]):
    """Creates a clef change on its anchor."""

    start: Bound[TemporalAnchor]
    staff: Staff
    clef: Clef
    octave_transposition: int
