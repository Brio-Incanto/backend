from typing import Annotated

from fastapi import APIRouter, Depends, Path

from piano_app.adapters.inbound.http import CurrentUser

from .requests import ChangeVisibilityRequest


def build_manage_router(*, current_user: CurrentUser) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/scores/{score_id}",
        tags=["score-manage"],
    )

    # TODO generalise? even without login discard at updating stage
    @router.patch(path="", status_code=200)
    async def change_visibility(
        score_id: Annotated[str, Path(description="The score ID")],
        actor_id: Annotated[str, Depends(current_user)],
        request: ChangeVisibilityRequest,
    ) -> None:
        raise NotImplementedError

    return router
