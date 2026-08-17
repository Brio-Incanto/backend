from pydantic import BaseModel, Field


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=8192)
    username: str | None = Field(default=None, min_length=1, max_length=64)
