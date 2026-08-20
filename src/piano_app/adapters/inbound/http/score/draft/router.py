from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from piano_app.adapters.inbound.http.current_user import CurrentUser
from piano_app.application.ports.score import DraftMeta
from piano_app.application.use_cases.score import DraftService
from piano_app.application.use_cases.score.draft.service import CreatedDraft
from piano_app.application.use_cases.score.shared import ScoreView

from .responses import DraftCardResponse, DraftCreatedResponse, GetDraftResponse


def build_draft_router(*, service: DraftService, current_user: CurrentUser) -> APIRouter:
    """Routes for the draft resource — create (from scratch or a score) and retrieve."""
    router: APIRouter = APIRouter(prefix="/drafts", tags=["draft"])

    @router.get(path="/{draft_id}", status_code=200)
    async def get_document(
        draft_id: Annotated[str, Path(description="The draft ID")],
        viewer_id: Annotated[str, Depends(current_user)],
    ) -> GetDraftResponse:
        view: ScoreView = await service.get_document(draft_id=draft_id, viewer_id=viewer_id)
        return GetDraftResponse.from_view(view)

    # Not paginated: list_author_drafts has no cursor mechanism yet (Redis SET
    # backing the hot-tier author index has no native ordering), and per-author
    # draft counts are expected to stay small
    @router.get(path="", status_code=200)
    async def get_mine(
        viewer_id: Annotated[str, Depends(current_user)],
    ) -> list[DraftCardResponse]:
        drafts: Sequence[DraftMeta] = await service.list_author_drafts(author_id=viewer_id)
        return [DraftCardResponse.from_meta(meta) for meta in drafts]

    # Brand-new rootless draft from a blank document (score_id NULL), an owner may
    # hold any number of these (NULLs are not equal under the unique constraint).
    @router.post(path="", status_code=201)
    async def create_draft(
        response: Response,
        actor_id: Annotated[str, Depends(current_user)],
    ) -> DraftCreatedResponse:
        created: CreatedDraft = await service.create_draft_from_scratch(actor_id=actor_id)
        response.headers["Location"] = f"/drafts/{created.draft_id}"
        return DraftCreatedResponse.from_created(created)

    # Create a draft seeded from a score's canon (a branch of that score's working copy).
    @router.post(path="/from-score/{score_id}", status_code=201)
    async def create_draft_from_score(
        response: Response,
        score_id: Annotated[str, Path(description="The score ID")],
        actor_id: Annotated[str, Depends(current_user)],
    ) -> DraftCreatedResponse:
        created: CreatedDraft = await service.create_draft_from_score(
            actor_id=actor_id,
            score_id=score_id,
        )
        response.headers["Location"] = f"/drafts/{created.draft_id}"
        return DraftCreatedResponse.from_created(created)

    return router
