from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.models.notation import Articulation
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteCarrierAction(CreateMutationAction[NoteCarrier]):
    """Creates a note carrier owned by a leaf or grace item."""

    owner: Bound[CarrierOwner]
    articulation: Articulation = Articulation.NONE


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteNoteCarrierAction(DeleteMutationAction[NoteCarrier]):
    """Deletes a note carrier."""
