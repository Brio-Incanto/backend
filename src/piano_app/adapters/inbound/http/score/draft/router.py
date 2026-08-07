from typing import Annotated

from fastapi import APIRouter, Header, Path, Response

from piano_app.application.use_cases.score import DraftService
from piano_app.application.use_cases.score.draft.service import CreatedDraft
from piano_app.application.use_cases.score.shared import ScoreView

from .responses import DraftCreatedResponse, GetDraftResponse


# TODO consider using Depends[]
def build_draft_router(*, service: DraftService) -> APIRouter:
    """Routes for the draft resource — create (from scratch or a score) and retrieve."""
    router: APIRouter = APIRouter(prefix="/drafts", tags=["draft"])

    @router.get(path="/{draft_id}", status_code=200)
    async def get_document(
        draft_id: Annotated[str, Path(description="The draft ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
    ) -> GetDraftResponse:
        view: ScoreView = await service.get_document(draft_id=draft_id, author_id=author_id)
        return GetDraftResponse(document=view.jsonify())

    # Brand-new rootless draft from a blank document (score_id NULL), an owner may
    # hold any number of these (NULLs are not equal under the unique constraint).
    @router.post(path="", status_code=201)
    async def create_draft(
        response: Response,
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
    ) -> DraftCreatedResponse:
        created: CreatedDraft = await service.create_draft_from_scratch(author_id=author_id)
        response.headers["Location"] = f"/drafts/{created.draft_id}"
        return DraftCreatedResponse(draft_id=created.draft_id, document=created.view.jsonify())

    # Create a draft seeded from a score's canon (a branch of that score's working copy).
    @router.post(path="/from-score/{score_id}", status_code=201)
    async def create_draft_from_score(
        response: Response,
        score_id: Annotated[str, Path(description="The score ID")],
        author_id: Annotated[str, Header(alias="X-Author-Id", description="The author ID")],
    ) -> DraftCreatedResponse:
        created: CreatedDraft = await service.create_draft_from_score(
            author_id=author_id,
            score_id=score_id,
        )
        response.headers["Location"] = f"/drafts/{created.draft_id}"
        return DraftCreatedResponse(draft_id=created.draft_id, document=created.view.jsonify())

    return router
