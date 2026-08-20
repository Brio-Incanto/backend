from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RotatedRefreshSession:
    user_id: str
    credential: str


class RefreshSessionRepository(Protocol):
    async def create(self, *, user_id: str) -> str: ...

    async def rotate(self, *, credential: str) -> RotatedRefreshSession | None:
        """Session lifecycle policy (the reason this exists as a port, not just
        a query): a credential is valid iff it matches a stored session AND
        that session has not expired. A valid rotation replaces the secret and
        slides the expiry window a full TTL forward from now — the window does
        not carry over from the session's original expiry. Returns ``None``
        (not an error) for an invalid, already-rotated, or expired credential.
        """
        ...

    async def revoke(self, *, credential: str) -> None: ...
