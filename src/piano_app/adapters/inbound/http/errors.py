from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from piano_app.application.errors import (
    DraftNotFoundError,
    DraftVersionConflictError,
    IdentityAlreadyLinkedError,
    InvalidAccessTokenError,
    InvalidExternalCredentialError,
    InvalidPaginationCursorError,
    InvalidRefreshTokenError,
    ScoreEditRejectedError,
    ScoreNotFoundError,
    ScoreNotOwnedError,
    ScoreVersionConflictError,
    UsernameConflictError,
    UsernameRequiredError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorMapping:
    error_type: type[Exception]
    status_code: int
    headers: dict[str, str] | None = None


_ERROR_MAPPINGS: tuple[ErrorMapping, ...] = (
    ErrorMapping(
        error_type=InvalidPaginationCursorError,
        status_code=status.HTTP_400_BAD_REQUEST,
    ),
    # RFC 7235: a missing/invalid bearer token gets the Bearer challenge
    # header. The other two 401s (bad sign-in credential, bad refresh cookie)
    # aren't a Bearer challenge — different request shape.
    ErrorMapping(
        error_type=InvalidAccessTokenError,
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    ),
    ErrorMapping(
        error_type=InvalidExternalCredentialError,
        status_code=status.HTTP_401_UNAUTHORIZED,
    ),
    ErrorMapping(
        error_type=InvalidRefreshTokenError,
        status_code=status.HTTP_401_UNAUTHORIZED,
    ),
    # the caller is refused, and only ever for a score they can already see
    ErrorMapping(
        error_type=ScoreNotOwnedError,
        status_code=status.HTTP_403_FORBIDDEN,
    ),
    ErrorMapping(
        error_type=DraftNotFoundError,
        status_code=status.HTTP_404_NOT_FOUND,
    ),
    ErrorMapping(
        error_type=ScoreNotFoundError,
        status_code=status.HTTP_404_NOT_FOUND,
    ),
    ErrorMapping(
        error_type=DraftVersionConflictError,
        status_code=status.HTTP_409_CONFLICT,
    ),
    ErrorMapping(
        error_type=IdentityAlreadyLinkedError,
        status_code=status.HTTP_409_CONFLICT,
    ),
    ErrorMapping(
        error_type=ScoreVersionConflictError,
        status_code=status.HTTP_409_CONFLICT,
    ),
    ErrorMapping(
        error_type=UsernameConflictError,
        status_code=status.HTTP_409_CONFLICT,
    ),
    ErrorMapping(
        error_type=ScoreEditRejectedError,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    ErrorMapping(
        error_type=UsernameRequiredError,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
)

_MAPPING_BY_TYPE: dict[type[Exception], ErrorMapping] = {
    mapping.error_type: mapping for mapping in _ERROR_MAPPINGS
}


# One handler is shared across every registered exception type.
# But FastAPI's handler signature is fixed to (request, exc), so
# the only way for it to know which status_code/headers apply is to look them
# up from the exception instance it actually receives, by its type
async def _handle_application_error(_request: Request, error: Exception) -> JSONResponse:
    mapping: ErrorMapping = _MAPPING_BY_TYPE[type(error)]
    return JSONResponse(
        status_code=mapping.status_code,
        content={"detail": str(error)},
        headers=mapping.headers,
    )


def register_exception_handlers(*, app: FastAPI) -> None:
    for mapping in _ERROR_MAPPINGS:
        app.add_exception_handler(
            exc_class_or_status_code=mapping.error_type,
            handler=_handle_application_error,
        )
