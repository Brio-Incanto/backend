from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from piano_app.adapters.inbound.http.current_user import CurrentUser, CurrentUserOptional
from piano_app.adapters.inbound.http.pagination import DEFAULT_LIMIT, MAX_LIMIT, PageResponse
from piano_app.application.ports import Page, ScoreMetaItem
from piano_app.application.use_cases.score import ScoreCatalogService
from piano_app.application.use_cases.score.catalog.service import ScoreItem

from .responses import ScoreCardResponse, ScoreResponse


def build_scores_router(
    *,
    service: ScoreCatalogService,
    current_user: CurrentUser,
    current_user_optional: CurrentUserOptional,
) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/scores", tags=["scores"])

    @router.get(path="", status_code=200)
    async def search_scores(
        q: Annotated[str | None, Query(description="Search over title and composer")] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
        cursor: Annotated[
            str | None,
            Query(description="Opaque page cursor from a previous page's next_cursor"),
        ] = None,
    ) -> PageResponse[ScoreCardResponse]:
        page: Page[ScoreMetaItem] = await service.search(query=q, limit=limit, cursor=cursor)
        return PageResponse.of(page, item=ScoreCardResponse.from_item)

    @router.get(path="/mine", status_code=200)
    async def search_mine(
        viewer_id: Annotated[str, Depends(current_user)],
        q: Annotated[str | None, Query(description="Search over title and composer")] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
        cursor: Annotated[
            str | None,
            Query(description="Opaque page cursor from a previous page's next_cursor"),
        ] = None,
    ) -> PageResponse[ScoreCardResponse]:
        page: Page[ScoreMetaItem] = await service.search_mine(
            viewer_id=viewer_id, query=q, limit=limit, cursor=cursor
        )
        return PageResponse.of(page, item=ScoreCardResponse.from_item)

    # Not paginated: a score's branch count is expected to stay small (organic
    # forks by other users), unlike the global catalog — revisit if that stops
    # holding. No tree here either — this is one flat level (direct children of
    # score_id), not a recursive derivation graph; nothing upstream needs deeper
    # branch nesting yet.
    @router.get(path="/{score_id}/branches", status_code=200)
    async def get_score_branches(
        score_id: Annotated[str, Path(description="The score ID")],
        viewer_id: Annotated[str | None, Depends(current_user_optional)],
    ) -> Sequence[ScoreCardResponse]:
        items: Sequence[ScoreMetaItem] = await service.get_score_branches(
            score_id=score_id, viewer_id=viewer_id
        )
        return [ScoreCardResponse.from_item(item) for item in items]

    @router.get(path="/{score_id}", status_code=200)
    async def get_score(
        score_id: Annotated[str, Path(description="The score ID")],
        viewer_id: Annotated[str | None, Depends(current_user_optional)],
    ) -> ScoreResponse:
        item: ScoreItem = await service.get_score(score_id=score_id, viewer_id=viewer_id)
        return ScoreResponse.from_item(item)

    return router
