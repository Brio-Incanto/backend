from piano_app.domain.score.document.models.material import CarrierOwner, NoteCarrier
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.document.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateNoteCarrierAction,
    DeleteNoteCarrierAction,
)


class CreateNoteCarrierHandler(MutationHandler[CreateNoteCarrierAction]):
    """Creates a note carrier on its owner (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateNoteCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> NoteCarrier:
        owner: CarrierOwner = resolve(action.owner)
        carrier: NoteCarrier = NoteCarrier.create(
            owner=owner,
            articulation=action.articulation,
            sink=sink,
        )
        return carrier


class DeleteNoteCarrierHandler(MutationHandler[DeleteNoteCarrierAction]):
    """Detaches a note carrier from its owner."""

    def handle(
        self,
        *,
        action: DeleteNoteCarrierAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        note_carrier: NoteCarrier = action.target
        note_carrier.detach(sink=sink)
        return None
