from dataclasses import dataclass
from typing import Protocol

from .external_identity_verifier import VerifiedIdentity


@dataclass(frozen=True, slots=True)
class UserProfile:
    user_id: str
    username: str


class UsernameConflictError(Exception):
    def __init__(self, *, username: str) -> None:
        super().__init__("Username is already in use.")
        self.username: str = username


class IdentityAlreadyLinkedError(Exception):
    """Raised on a concurrent link of the same external identity — e.g. two
    taps of "sign in" racing each other before either commits."""

    def __init__(self) -> None:
        super().__init__("Identity is already linked to a user.")


class IdentityRepository(Protocol):
    async def create_user(self, *, username: str) -> UserProfile:
        """Raises ``UsernameConflictError`` if ``username`` is already taken."""
        ...

    async def add_identity(self, *, user_id: str, identity: VerifiedIdentity) -> None:
        """Raises ``IdentityAlreadyLinkedError`` if ``identity`` is already linked
        to a user (including a concurrent link racing this one)."""
        ...

    async def find_user_id(self, *, identity: VerifiedIdentity) -> str | None: ...

    async def find_user(self, *, user_id: str) -> UserProfile | None: ...
