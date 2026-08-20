from dataclasses import dataclass
from typing import Protocol

from .external_identity_verifier import VerifiedIdentity


@dataclass(frozen=True, slots=True)
class UserProfile:
    user_id: str
    username: str


class UsernameAlreadyExistsError(Exception):
    def __init__(self, *, username: str) -> None:
        super().__init__(f"Username {username!r} already exists.")
        self.username: str = username


class IdentityLinkConflictError(Exception):
    """Raised when an external identity is already linked."""


class IdentityRepository(Protocol):
    async def create_user(self, *, username: str) -> UserProfile:
        """Raises ``UsernameAlreadyExistsError`` if ``username`` is already taken."""
        ...

    async def add_identity(self, *, user_id: str, identity: VerifiedIdentity) -> None:
        """Raises ``IdentityLinkConflictError`` if ``identity`` is already linked
        to a user (including a concurrent link racing this one)."""
        ...

    async def find_user_id(self, *, identity: VerifiedIdentity) -> str | None: ...

    async def find_user(self, *, user_id: str) -> UserProfile | None: ...
