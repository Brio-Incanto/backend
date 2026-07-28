from dataclasses import dataclass

from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
)
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTemporalAnchorRequest(CreateMutationRequest[TemporalAnchor]):
    """A request to create a temporal anchor at a measure position."""

    measure: Measure
    position: MeasurePosition


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTemporalAnchorRequest(DeleteMutationRequest[TemporalAnchor]):
    """A request to delete a temporal anchor."""
