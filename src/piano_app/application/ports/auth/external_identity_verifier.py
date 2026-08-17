from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """The sole product of ``ExternalIdentityVerifier.verify`` — ``IdentityRepository``
    accepts it as a parameter (a lookup/link key) but never produces one itself,
    so this is a producer→consumer dependency, not joint ownership."""

    authority: str
    subject: str


class InvalidExternalCredentialError(Exception):
    def __init__(self) -> None:
        super().__init__("External identity credential is invalid.")


class ExternalIdentityVerifier(Protocol):
    async def verify(self, *, credential: str) -> VerifiedIdentity:
        """Raises ``InvalidExternalCredentialError`` if the credential fails verification."""
        ...
