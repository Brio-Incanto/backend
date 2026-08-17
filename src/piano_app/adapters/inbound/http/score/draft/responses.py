from pydantic import BaseModel, Field

from piano_app.application.use_cases.score.draft.service import CreatedDraft
from piano_app.application.use_cases.score.shared import ScoreView


class DraftCreatedResponse(BaseModel):
    draft_id: str = Field(description="The newly created draft's id")
    document: dict[str, object] = Field(description="The draft's initial document view")

    @classmethod
    def from_created(cls, created: CreatedDraft) -> DraftCreatedResponse:
        return cls(draft_id=created.draft_id, document=created.view.jsonify())


class GetDraftResponse(BaseModel):
    document: dict[str, object] = Field(description="The draft's document view")

    @classmethod
    def from_view(cls, view: ScoreView) -> GetDraftResponse:
        return cls(document=view.jsonify())
