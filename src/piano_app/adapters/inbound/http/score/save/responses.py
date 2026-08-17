from pydantic import BaseModel, Field


class ScoreSavedResponse(BaseModel):
    score_id: str = Field(description="The newly created score's id")

    @classmethod
    def from_score_id(cls, score_id: str) -> ScoreSavedResponse:
        return cls(score_id=score_id)
