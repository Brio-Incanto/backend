from fastapi import APIRouter

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
    TieNotesCommand,
)
from piano_app.application.use_cases.score import ScoreEditView, ScoreMutationService


def build_edit_router(*, service: ScoreMutationService) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/scores/{score_id}/edit",
        tags=["score-edit"],
    )

    @router.get("/document")
    def get_document(score_id: str) -> ScoreEditView:
        return service.get_document(edit_id=score_id)

    @router.post("/notes")
    def insert_note(
        score_id: str,
        command: InsertNoteCommand,
    ) -> ScoreEditView:
        return service.insert_note(
            edit_id=score_id,
            command=command,
        )

    @router.post("/ties")
    def tie_notes(
        score_id: str,
        command: TieNotesCommand,
    ) -> ScoreEditView:
        return service.tie_notes(
            edit_id=score_id,
            command=command,
        )

    @router.post("/batch-delete")
    def delete_batch(
        score_id: str,
        command: DeleteBatchCommand,
    ) -> ScoreEditView:
        return service.delete_batch(
            edit_id=score_id,
            command=command,
        )

    @router.post("/undo")
    def undo(score_id: str) -> ScoreEditView:
        return service.undo(edit_id=score_id)

    @router.post("/redo")
    def redo(score_id: str) -> ScoreEditView:
        return service.redo(edit_id=score_id)

    return router
