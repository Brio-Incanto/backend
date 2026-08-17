from typing import Annotated

from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from piano_app.application.errors import InvalidAccessTokenError
from piano_app.application.ports.auth import AccessTokenService
from piano_app.application.ports.auth import InvalidAccessTokenError as PortInvalidAccessTokenError

_BEARER: HTTPBearer = HTTPBearer(auto_error=False)


class CurrentUser:
    """Resolves and REQUIRES an authenticated caller: returns the user id, or
    raises 401 if the bearer token is missing or invalid.
    """

    def __init__(self, *, access_tokens: AccessTokenService) -> None:
        self._access_tokens: AccessTokenService = access_tokens

    async def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Security(_BEARER),
        ],
    ) -> str:
        # HTTPBearer(auto_error=False) returns None for a missing or non-"bearer"
        # header; verify() raises the port's InvalidAccessTokenError for an
        # invalid token — translated below, this dependency never lets that
        # port-owned type cross into the HTTP layer.
        if credentials is None:
            raise InvalidAccessTokenError

        try:
            return self._access_tokens.verify(token=credentials.credentials)
        except PortInvalidAccessTokenError as error:
            raise InvalidAccessTokenError from error


class CurrentUserOptional:
    """Resolves the caller from an OPTIONAL bearer token: no token -> ``None``
    (anonymous); present-but-invalid token -> still 401 (``verify`` raises) — an
    unreadable token is a client error, not anonymity. For endpoints that work
    anonymously but widen/annotate when the caller is known."""

    def __init__(self, *, access_tokens: AccessTokenService) -> None:
        self._access_tokens: AccessTokenService = access_tokens

    async def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Security(_BEARER),
        ],
    ) -> str | None:
        if credentials is None:
            return None

        try:
            return self._access_tokens.verify(token=credentials.credentials)
        except PortInvalidAccessTokenError as error:
            raise InvalidAccessTokenError from error
