from dataclasses import dataclass

from piano_app.domain.score.document.models.context import Context
from piano_app.domain.score.document.services.mutation.instructions.requests.base import (
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteContextRequest(DeleteMutationRequest[Context]):
    """A request to delete a context — point or span, any scope. A context owns no
    children, so unlike most delete requests this never cascades."""
