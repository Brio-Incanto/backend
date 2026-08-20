from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_in_seconds: int


class AccessTokenVerificationError(Exception):
    """Raised when an access token cannot be verified."""


class AccessTokenService(Protocol):
    def issue(self, *, user_id: str) -> AccessToken:
        """Returns a new access token for the given user ID."""
        ...

    def verify(self, *, token: str) -> str:
        """Raises ``AccessTokenVerificationError`` if verification fails."""
        ...
