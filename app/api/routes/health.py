"""Liveness endpoint used by container healthchecks and CI smoke tests."""

from fastapi import APIRouter

from app.schemas.common import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[dict[str, str]])
async def health() -> SuccessResponse[dict[str, str]]:
    """Report that the service is up."""
    return SuccessResponse(data={"service": "chat-api", "status": "ok"})
