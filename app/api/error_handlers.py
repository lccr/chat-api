"""Centralized error handling.

Translates domain exceptions and framework validation errors into the
uniform error envelope, guaranteeing no endpoint leaks a stack trace or
FastAPI's default 422 body.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError
from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def _envelope(code: str, message: str, details: object = None) -> dict[str, object]:
    detail = ErrorDetail(code=code, message=message, details=details)
    return ErrorResponse(error=detail).model_dump()


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Map any ``DomainError`` to its declared status and error code."""
    logger.warning(
        "Domain error on %s %s: %s",
        request.method,
        request.url.path,
        exc.code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Translate Pydantic validation failures into the error envelope."""
    details = [
        f"{'.'.join(str(loc) for loc in err['loc'] if loc != 'body')}: {err['msg']}"
        for err in exc.errors()
    ]
    logger.warning("Validation failed on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope("INVALID_FORMAT", "Invalid message format", details),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler: log everything, expose nothing."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("INTERNAL_ERROR", "An unexpected error occurred"),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach all handlers to the application."""
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
