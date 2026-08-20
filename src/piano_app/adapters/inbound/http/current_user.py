from typing import Annotated

from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from piano_app.application.use_cases.auth import AuthService

_BEARER: HTTPBearer = HTTPBearer(auto_error=False)


class CurrentUser:
    """Resolves and REQUIRES an authenticated caller: returns the user id, or
    raises 401 if the bearer token is missing or invalid.
    """

    def __init__(self, *, service: AuthService) -> None:
        self._service: AuthService = service

    async def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Security(_BEARER),
        ],
    ) -> str:
        # HTTPBearer(auto_error=False) returns None for a missing or non-"bearer"
        token: str | None = None if credentials is None else credentials.credentials
        return self._service.authenticate_access_token(token=token)


class CurrentUserOptional:
    """Resolves the caller from an OPTIONAL bearer token: no token -> ``None``
    (anonymous); present-but-invalid token -> still 401 (``verify`` raises) — an
    unreadable token is a client error, not anonymity. For endpoints that work
    anonymously but widen/annotate when the caller is known."""

    def __init__(self, *, service: AuthService) -> None:
        self._service: AuthService = service

    async def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Security(_BEARER),
        ],
    ) -> str | None:
        if credentials is None:
            return None

        return self._service.authenticate_access_token(token=credentials.credentials)
