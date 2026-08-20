from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """The sole product of ``ExternalIdentityVerifier.verify`` — ``IdentityRepository``
    accepts it as a parameter (a lookup/link key) but never produces one itself,
    so this is a producer→consumer dependency, not joint ownership."""

    authority: str
    subject: str


class ExternalCredentialVerificationError(Exception):
    """Raised when an external identity credential cannot be verified."""


class ExternalIdentityVerifier(Protocol):
    async def verify(self, *, credential: str) -> VerifiedIdentity:
        """Raises ``ExternalCredentialVerificationError`` if verification fails."""
        ...
