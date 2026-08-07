from pydantic import BaseModel, Field


class ScoreSavedResponse(BaseModel):
    score_id: str = Field(description="The newly created score's id")
