from pydantic import BaseModel, Field


class ChangeVisibilityRequest(BaseModel):
    is_public: bool = Field(description="Whether the score should be public")
