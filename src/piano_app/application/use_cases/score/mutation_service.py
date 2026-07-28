from collections import defaultdict
from collections.abc import Sequence

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
)
from piano_app.application.errors import EditHistoryEmptyError, EditRejectedError
from piano_app.application.ports import DraftStore
from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.services.mutation.compiler import MutationCompiler
from piano_app.domain.score.services.mutation.engine import MutationEngine
from piano_app.domain.score.services.mutation.engine.log import MutationLog
from piano_app.domain.score.services.mutation.instructions import (
    MutationRejectedError,
    MutationRequest,
)

from .undo_redo_stack import UndoRedoStack
from .view import ScoreEditView, build_score_edit_view


class ScoreMutationService:
    """Application orchestration for mutations of a transient score draft.

    The service depends only on the draft-store port. The current outbound adapter
    is in-memory; a cache-backed adapter can replace it without changing this use case.
    Persisting a finished draft is a separate future application use case.
    """

    def __init__(
        self,
        *,
        engine: MutationEngine,
        compiler: MutationCompiler,
        store: DraftStore,
        undo: defaultdict[str, UndoRedoStack],
    ) -> None:
        self._engine: MutationEngine = engine
        self._compiler: MutationCompiler = compiler
        self._store: DraftStore = store
        self._undo: defaultdict[str, UndoRedoStack] = undo

    def get_document(self, *, edit_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=edit_id)
        return build_score_edit_view(document=document, score_id=edit_id)

    def insert_note(self, *, edit_id: str, command: InsertNoteCommand) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=edit_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_insert_note(
                document=document,
                intent=command,
            )
            self._run(edit_id=edit_id, document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        return build_score_edit_view(document=document, score_id=edit_id)

    def tie_notes(self, *, edit_id: str, command: InsertNoteCommand):

    def delete_batch(self, *, edit_id: str, command: DeleteBatchCommand) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=edit_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_delete_batch(
                document=document,
                intent=command,
            )
            self._run(edit_id=edit_id, document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        return build_score_edit_view(document=document, score_id=edit_id)

    def undo(self, *, edit_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=edit_id)
        if not self._undo[edit_id].undo():
            raise EditHistoryEmptyError(operation="undo")

        return build_score_edit_view(document=document, score_id=edit_id)

    def redo(self, *, edit_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=edit_id)
        if not self._undo[edit_id].redo():
            raise EditHistoryEmptyError(operation="redo")

        return build_score_edit_view(document=document, score_id=edit_id)

    def _run(
        self,
        *,
        edit_id: str,
        document: ScoreDocument,
        requests: Sequence[MutationRequest],
    ) -> None:
        log: MutationLog = self._engine.process(document=document, requests=requests)
        self._store.save(draft_id=edit_id, document=document)
        self._undo[edit_id].push(log)
