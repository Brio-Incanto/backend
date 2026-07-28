from fastapi import APIRouter

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
    TieNotesCommand,
)
from piano_app.application.use_cases.score import ScoreEditService


def build_edit_router(*, service: ScoreEditService) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/scores/{score_id}/edit",
        tags=["score-edit"],
    )

    # `score_id` (the public, URL-facing identity) is passed through as `draft_id`
    # (the service/store's working-copy identity) — today a 1:1 mapping, but the
    # translation point where a future `/scores/{id}/branches/{branch}/edit` would
    # resolve `score_id` + branch into a real `draft_id`.

    @router.get("/document")
    def get_document(score_id: str) -> dict[str, object]:
        return service.get_document(draft_id=score_id)

    @router.post("/notes")
    def insert_note(
        score_id: str,
        command: InsertNoteCommand,
    ) -> dict[str, object]:
        return service.insert_note(
            draft_id=score_id,
            command=command,
        )

    @router.post("/ties")
    def tie_notes(
        score_id: str,
        command: TieNotesCommand,
    ) -> dict[str, object]:
        return service.tie_notes(
            draft_id=score_id,
            command=command,
        )

    @router.post("/batch-delete")
    def delete_batch(
        score_id: str,
        command: DeleteBatchCommand,
    ) -> dict[str, object]:
        return service.delete_batch(
            draft_id=score_id,
            command=command,
        )

    @router.post("/undo")
    def undo(score_id: str) -> dict[str, object]:
        return service.undo(draft_id=score_id)

    @router.post("/redo")
    def redo(score_id: str) -> dict[str, object]:
        return service.redo(draft_id=score_id)

    return router
