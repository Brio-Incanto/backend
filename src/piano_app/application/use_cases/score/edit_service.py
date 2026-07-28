from collections import defaultdict
from collections.abc import Sequence

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
    TieNotesCommand,
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


class ScoreEditService:
    """Application orchestration for editing a transient score draft.

    Runs edits through the domain mutation engine, keyed by draft id (the
    working copy — see ``DraftStore``). The current outbound adapter is
    in-memory; a cache-backed adapter can replace it without changing this use
    case. Persisting a finished draft is a separate future application use case.
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

    def get_document(self, *, draft_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        return build_score_edit_view(document=document, score_id=draft_id)

    def insert_note(self, *, draft_id: str, command: InsertNoteCommand) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_insert_note(
                document=document,
                intent=command,
            )
            self._run(draft_id=draft_id, document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        return build_score_edit_view(document=document, score_id=draft_id)

    def tie_notes(self, *, draft_id: str, command: TieNotesCommand) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_tie_notes(
                document=document,
                intent=command,
            )
            self._run(draft_id=draft_id, document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        return build_score_edit_view(document=document, score_id=draft_id)

    def delete_batch(self, *, draft_id: str, command: DeleteBatchCommand) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        try:
            requests: Sequence[MutationRequest] = self._compiler.compile_delete_batch(
                document=document,
                intent=command,
            )
            self._run(draft_id=draft_id, document=document, requests=requests)
        except MutationRejectedError as error:
            raise EditRejectedError(reason=error.reason) from error

        return build_score_edit_view(document=document, score_id=draft_id)

    def undo(self, *, draft_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        if not self._undo[draft_id].undo():
            raise EditHistoryEmptyError(operation="undo")

        return build_score_edit_view(document=document, score_id=draft_id)

    def redo(self, *, draft_id: str) -> ScoreEditView:
        document: ScoreDocument = self._store.load(draft_id=draft_id)
        if not self._undo[draft_id].redo():
            raise EditHistoryEmptyError(operation="redo")

        return build_score_edit_view(document=document, score_id=draft_id)

    def _run(
        self,
        *,
        draft_id: str,
        document: ScoreDocument,
        requests: Sequence[MutationRequest],
    ) -> None:
        log: MutationLog = self._engine.process(document=document, requests=requests)
        self._store.save(draft_id=draft_id, document=document)
        self._undo[draft_id].push(log)
