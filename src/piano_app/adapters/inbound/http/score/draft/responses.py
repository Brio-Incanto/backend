from pydantic import BaseModel, Field


class DraftCreatedResponse(BaseModel):
    draft_id: str = Field(description="The newly created draft's id")
    document: dict[str, object] = Field(description="The draft's initial document view")


class GetDraftResponse(BaseModel):
    document: dict[str, object] = Field(description="The draft's document view")
