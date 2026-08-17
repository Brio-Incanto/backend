from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_in_seconds: int


class InvalidAccessTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Access token is invalid or expired.")


class AccessTokenService(Protocol):
    def issue(self, *, user_id: str) -> AccessToken:
        """Returns a new access token for the given user ID."""
        ...

    def verify(self, *, token: str) -> str:
        """Raises ``InvalidAccessTokenError`` if the token is invalid, expired, or malformed."""
        ...
