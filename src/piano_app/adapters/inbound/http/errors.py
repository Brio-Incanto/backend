from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from piano_app.application.errors import (
    EditDraftNotFoundError,
    EditHistoryEmptyError,
    EditRejectedError,
)

_APPLICATION_ERROR_STATUS: dict[type[Exception], int] = {
    EditDraftNotFoundError: status.HTTP_404_NOT_FOUND,
    EditHistoryEmptyError: status.HTTP_409_CONFLICT,
    EditRejectedError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


async def application_error_handler(
    _request: Request,
    error: Exception,
) -> JSONResponse:
    status_code: int = _APPLICATION_ERROR_STATUS[type(error)]
    content: dict[str, str] = {"detail": str(error)}
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(*, app: FastAPI) -> None:
    for error_type in _APPLICATION_ERROR_STATUS:
        app.add_exception_handler(error_type, application_error_handler)
