from typing import Annotated

from fastapi import APIRouter, Body, Header, Path

from piano_app.application.use_cases.score import ScoreEditService
from piano_app.application.use_cases.score.shared import ScoreView

from .requests import DeleteBatchRequest, InsertNoteRequest, TieNotesRequest
from .responses import ScoreEditedResponse


# TODO consider using Depends[]
def build_edit_router(*, service: ScoreEditService) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/drafts/{draft_id}/edit",
        tags=["score-edit"],
    )

    @router.post(path="/notes", status_code=200)
    async def insert_note(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
        request: Annotated[InsertNoteRequest, Body(description="The insert command")],
    ) -> ScoreEditedResponse:
        view: ScoreView = await service.insert_note(
            draft_id=draft_id,
            author_id=author_id,
            command=request.to_command(),
        )
        return ScoreEditedResponse(document=view.jsonify())

    @router.post(path="/ties", status_code=200)
    async def tie_notes(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
        request: Annotated[TieNotesRequest, Body(description="The tie command")],
    ) -> ScoreEditedResponse:
        view: ScoreView = await service.tie_notes(
            draft_id=draft_id,
            author_id=author_id,
            command=request.to_command(),
        )
        return ScoreEditedResponse(document=view.jsonify())

    @router.post(path="/batch-delete", status_code=200)
    async def delete_batch(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
        request: Annotated[DeleteBatchRequest, Body(description="The delete command")],
    ) -> ScoreEditedResponse:
        view: ScoreView = await service.delete_batch(
            draft_id=draft_id, author_id=author_id, command=request.to_command()
        )
        return ScoreEditedResponse(document=view.jsonify())

    @router.post(path="/undo", status_code=200)
    async def undo(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
    ) -> ScoreEditedResponse:
        view: ScoreView = await service.undo(
            draft_id=draft_id,
            author_id=author_id,
        )
        return ScoreEditedResponse(document=view.jsonify())

    @router.post(path="/redo", status_code=200)
    async def redo(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
    ) -> ScoreEditedResponse:
        view: ScoreView = await service.redo(
            draft_id=draft_id,
            author_id=author_id,
        )
        return ScoreEditedResponse(document=view.jsonify())

    return router
