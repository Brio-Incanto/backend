from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.carrier_owner import CarrierOwner
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.instructions.actions.material.note_carrier import (
    CreateNoteCarrierAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class CreateNoteCarrierHandler:
    """Creates a note carrier on its owner (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateNoteCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        owner: CarrierOwner = resolve(action.owner)
        carrier: NoteCarrier = NoteCarrier.create(
            owner=owner,
            articulation=action.articulation,
            sink=sink,
        )
        return carrier
