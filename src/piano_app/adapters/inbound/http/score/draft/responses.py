from datetime import datetime

from pydantic import BaseModel, Field

from piano_app.application.ports.score import DraftMeta
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


class DraftCardResponse(BaseModel):
    """Metadata-only card for listing — never carries the document, matching
    ScoreCardResponse's light-listing shape on the score side."""

    draft_id: str = Field(description="The draft's id")
    title: str = Field(description="The draft's title")
    ref_score_id: str | None = Field(
        default=None, description="The score this draft branches from, if any"
    )
    updated_at: datetime = Field(description="The draft's last update date")

    @classmethod
    def from_meta(cls, meta: DraftMeta) -> DraftCardResponse:
        return cls(
            draft_id=meta.draft_id,
            title=meta.title,
            ref_score_id=meta.ref_score_id,
            updated_at=meta.updated_at,
        )
