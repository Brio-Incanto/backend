from dataclasses import dataclass

from piano_app.domain.score.document.models.context import KeySignatureChange, KeySignatureSymbol
from piano_app.domain.score.document.models.structural import Staff, TemporalAnchor
from piano_app.domain.score.document.services.mutation.instructions import Bound
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateKeySignatureChangeAction(CreateMutationAction[KeySignatureChange]):
    """Creates a key signature change on its anchor."""

    start: Bound[TemporalAnchor]
    staff: Staff
    symbols: tuple[KeySignatureSymbol, ...]
