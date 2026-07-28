from dataclasses import dataclass

from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
)
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTemporalAnchorAction(CreateMutationAction[TemporalAnchor]):
    """Creates a temporal anchor at a measure position."""

    measure: Measure
    position: MeasurePosition


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTemporalAnchorAction(DeleteMutationAction[TemporalAnchor]):
    """Deletes a temporal anchor."""
