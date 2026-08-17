from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from piano_app.adapters.inbound.http.current_user import CurrentUser
from piano_app.application.use_cases.score import SaveScoreService

from .requests import CreateScoreRequest
from .responses import ScoreSavedResponse


def build_save_router(*, service: SaveScoreService, current_user: CurrentUser) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/drafts/{draft_id}",
        tags=["draft-save"],
    )

    # Overwrite the canon score this draft derives from (owner only)
    @router.post(path="/promote", status_code=200)
    async def promote(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Depends(current_user)],
    ) -> ScoreSavedResponse:
        updated_id: str = await service.promote(draft_id=draft_id, author_id=author_id)
        return ScoreSavedResponse.from_score_id(updated_id)

    @router.post(path="/branches", status_code=201)
    async def create_branch(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Depends(current_user)],
        request: Annotated[CreateScoreRequest, Body(description="The create score request")],
    ) -> ScoreSavedResponse:
        created_id: str = await service.create_branch(
            draft_id=draft_id,
            author_id=author_id,
            command=request.to_command(),
        )
        return ScoreSavedResponse.from_score_id(created_id)

    return router
