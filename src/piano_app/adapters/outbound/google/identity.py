import asyncio
from collections.abc import Mapping
from typing import Any

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from piano_app.application.ports.auth import (
    ExternalCredentialVerificationError,
    VerifiedIdentity,
)


class GoogleIdentityVerifier:
    # OIDC Issuer
    _AUTHORITY: str = "https://accounts.google.com"

    # allowed audiences for the specified in the config client, e.g. Web, Android, iOS
    def __init__(self, *, allowed_audiences: frozenset[str]) -> None:
        if not allowed_audiences:
            raise ValueError("At least one Google client ID must be configured.")

        self._allowed_audiences: frozenset[str] = allowed_audiences

    async def verify(self, *, credential: str) -> VerifiedIdentity:
        try:
            claims: Mapping[str, Any] = await asyncio.to_thread(
                id_token.verify_oauth2_token,
                id_token=credential,
                request=Request(),
                audience=list(self._allowed_audiences),
            )
        except TransportError:
            raise
        except GoogleAuthError, ValueError:
            raise ExternalCredentialVerificationError from None

        subject: object = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ExternalCredentialVerificationError

        return VerifiedIdentity(
            authority=self._AUTHORITY,
            subject=subject,
        )
