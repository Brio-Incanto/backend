from pydantic import BaseModel, Field


class ScoreEditedResponse(BaseModel):
    document: dict[str, object] = Field(description="The new document view")
