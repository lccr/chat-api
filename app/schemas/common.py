"""Uniform response envelopes.

Every endpoint responds with the same top-level shape, which makes client
handling and automated consumption predictable:

Success: ``{"status": "success", "data": {...}}``
Error:   ``{"status": "error", "error": {"code", "message", "details"}}``
"""

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Envelope for successful responses."""

    status: Literal["success"] = "success"
    data: DataT


class ErrorDetail(BaseModel):
    """Machine-readable error description."""

    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    """Envelope for error responses."""

    status: Literal["error"] = "error"
    error: ErrorDetail
