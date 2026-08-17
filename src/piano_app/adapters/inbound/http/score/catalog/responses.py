from datetime import datetime

from pydantic import BaseModel, Field

from piano_app.application.ports import ScoreMetaItem
from piano_app.application.use_cases.score.catalog.service import ScoreItem


class ScoreCardResponse(BaseModel):
    id: str = Field(description="The score's id")
    title: str = Field(description="The score's title")
    composer: str | None = Field(default=None, description="The score's composer")
    author_id: str | None = Field(default=None, description="The score's author id")
    author_name: str | None = Field(default=None, description="The score's author name")
    is_public: bool = Field(default=False, description="Whether the score is public")
    created_at: datetime = Field(description="The score's creation date")
    updated_at: datetime = Field(description="The score's last update date")

    @classmethod
    def from_item(cls, item: ScoreMetaItem) -> ScoreCardResponse:
        return cls(
            id=item.id,
            title=item.title,
            composer=item.composer,
            author_id=item.author_id,
            author_name=item.author_name,
            is_public=item.is_public,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class ScoreResponse(BaseModel):
    id: str = Field(description="The score's id")
    title: str = Field(description="The score's title")
    composer: str | None = Field(default=None, description="The score's composer")
    author_id: str | None = Field(default=None, description="The score's author id")
    author_name: str | None = Field(default=None, description="The score's author name")
    derived_from_id: str | None = Field(default=None, description="The parent score's id, if any")
    is_public: bool = Field(default=False, description="Whether the score is public")
    created_at: datetime = Field(description="The score's creation date")
    updated_at: datetime = Field(description="The score's last update date")
    document: dict[str, object] = Field(description="The score's document view")

    @classmethod
    def from_item(cls, item: ScoreItem) -> ScoreResponse:
        return cls(
            id=item.id,
            title=item.title,
            composer=item.composer,
            author_id=item.author_id,
            author_name=item.author_name,
            derived_from_id=item.derived_from_id,
            is_public=item.is_public,
            created_at=item.created_at,
            updated_at=item.updated_at,
            document=item.document.jsonify(),
        )
