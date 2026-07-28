from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.models.notation import Articulation
from piano_app.domain.score.services.mutation.instructions.actions import CreateMutationAction
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteCarrierAction(CreateMutationAction[NoteCarrier]):
    """Creates a note carrier owned by a leaf or grace item.

    The owner may be existing or produced earlier in the plan; the carrier is
    published through ``out``.
    """

    owner: Bound[CarrierOwner]
    articulation: Articulation = Articulation.NONE
