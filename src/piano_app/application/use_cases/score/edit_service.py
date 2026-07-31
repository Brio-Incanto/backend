from collections.abc import Sequence

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
    TieNotesCommand,
)
from piano_app.application.errors import (
    EditDraftNotFoundError,
    EditRejectedError,
)
from piano_app.application.ports import DraftHistory
from piano_app.application.ports.draft_store import DraftNotFoundError
from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.services.mutation.compiler import MutationCompiler
from piano_app.domain.score.services.mutation.engine import MutationEngine
from piano_app.domain.score.services.mutation.instructions import (
    MutationRejectedError,
    MutationRequest,
)

from .view import ScoreEditView


class ScoreEditService:
    """Application orchestration for editing a transient score draft.

    Runs edits through the domain mutation engine, keyed by draft id (the
    working copy — see ``DraftHistory``). The current outbound adapter is
    in-memory; a cache-backed adapter can replace it without changing this use
    case. Persisting a finished draft is a separate future application use case.
    """

    def __init__(
        self,
        *,
        engine: MutationEngine,
        compiler: MutationCompiler,
        history: DraftHistory,
    ) -> None:
        self._engine: MutationEngine = engine
        self._compiler: MutationCompiler = compiler
        self._drafts_history: DraftHistory = history

    async def get_document(self, *, draft_id: str) -> dict[str, object]:
        document: ScoreDocument = await self._load(draft_id=draft_id)
        return ScoreEditView(document=document).jsonify()

    async def insert_note(
        self,
        *,
        draft_id: str,
        command: InsertNoteCommand,
    ) -> dict[str, object]:
        document: ScoreDocument = await self._load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_insert_note(
                document=document,
                intent=command,
            )
            self._run(document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        await self._drafts_history.commit(draft_id=draft_id, document=document)
        return ScoreEditView(document=document).jsonify()

    async def tie_notes(
        self,
        *,
        draft_id: str,
        command: TieNotesCommand,
    ) -> dict[str, object]:
        document: ScoreDocument = await self._load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_tie_notes(
                document=document,
                intent=command,
            )
            self._run(document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        await self._drafts_history.commit(draft_id=draft_id, document=document)
        return ScoreEditView(document=document).jsonify()

    async def delete_batch(
        self,
        *,
        draft_id: str,
        command: DeleteBatchCommand,
    ) -> dict[str, object]:
        document: ScoreDocument = await self._load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_delete_batch(
                document=document,
                intent=command,
            )
            self._run(document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        await self._drafts_history.commit(draft_id=draft_id, document=document)
        return ScoreEditView(document=document).jsonify()

    async def undo(self, *, draft_id: str) -> dict[str, object]:
        # An empty history is a successful no-op, not an error: the request was
        # understood and the draft is left in a valid state.
        # Return the current view either way
        try:
            await self._drafts_history.undo(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

        return ScoreEditView(document=await self._load(draft_id=draft_id)).jsonify()

    async def redo(self, *, draft_id: str) -> dict[str, object]:
        try:
            await self._drafts_history.redo(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

        return ScoreEditView(document=await self._load(draft_id=draft_id)).jsonify()

    async def _load(self, *, draft_id: str) -> ScoreDocument:
        try:
            return await self._drafts_history.load(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

    # TODO consider moving commit here
    def _run(self, *, document: ScoreDocument, requests: Sequence[MutationRequest]) -> None:
        self._engine.process(document=document, requests=requests)
