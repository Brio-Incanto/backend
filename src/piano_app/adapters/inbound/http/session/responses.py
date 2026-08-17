from typing import Literal

from pydantic import BaseModel

from piano_app.application.ports.auth import UserProfile
from piano_app.application.use_cases.auth import AuthSession


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

    @classmethod
    def from_session(cls, session: AuthSession) -> AccessTokenResponse:
        return cls(
            access_token=session.access_token.value,
            expires_in=session.access_token.expires_in_seconds,
        )


class CurrentUserResponse(BaseModel):
    user_id: str
    username: str

    @classmethod
    def from_profile(cls, profile: UserProfile) -> CurrentUserResponse:
        return cls(user_id=profile.user_id, username=profile.username)
