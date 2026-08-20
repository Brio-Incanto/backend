from typing import Annotated

from fastapi import APIRouter, Path, Query

from piano_app.adapters.inbound.http.pagination import DEFAULT_LIMIT, MAX_LIMIT, PageResponse
from piano_app.application.ports import Page, ScoreMetaItem
from piano_app.application.use_cases.score import ScoreCatalogService

from ..catalog.responses import ScoreCardResponse


def build_authors_router(*, service: ScoreCatalogService) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/authors", tags=["authors"])

    @router.get(path="/{author_id}/scores", status_code=200)
    async def search_author_scores(
        author_id: Annotated[str, Path(description="The author ID")],
        q: Annotated[str | None, Query(description="Search over title and composer")] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
        cursor: Annotated[
            str | None,
            Query(description="Opaque page cursor from a previous page's next_cursor"),
        ] = None,
    ) -> PageResponse[ScoreCardResponse]:
        page: Page[ScoreMetaItem] = await service.search_author_scores(
            author_id=author_id,
            query=q,
            limit=limit,
            cursor=cursor,
        )
        return PageResponse.of(page, item=ScoreCardResponse.from_item)

    return router
