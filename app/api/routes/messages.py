"""Message endpoints.

Thin controllers: they translate HTTP to service calls and back. All business
logic lives in the service and pipeline; validation lives in the schemas.
"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import MessageServiceDep, require_api_key
from app.core.rate_limit import default_limit, limiter
from app.models.message import Message
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.message import MessageCreate, MessageMetadata, MessageResponse, Sender

router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
    dependencies=[Depends(require_api_key)],
)


def _to_response(message: Message) -> MessageResponse:
    """Map an ORM message to its API representation."""
    return MessageResponse(
        message_id=message.message_id,
        session_id=message.session_id,
        content=message.content,
        timestamp=message.timestamp,
        # DB stores sender as str; it was constrained to a valid Sender on
        # write (schema validation), so narrowing back is safe here.
        sender=cast(Sender, message.sender),
        metadata=MessageMetadata(
            word_count=message.word_count,
            character_count=message.character_count,
            processed_at=message.processed_at,
        ),
    )


@router.post(
    "",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(default_limit())
def create_message(
    request: Request,
    payload: MessageCreate,
    service: MessageServiceDep,
) -> SuccessResponse[MessageResponse]:
    """Validate, process and store an incoming chat message."""
    message = service.create_message(payload)
    return SuccessResponse(data=_to_response(message))


@router.get(
    "/search",
    response_model=SuccessResponse[PaginatedData[MessageResponse]],
)
@limiter.limit(default_limit())
def search_messages(
    request: Request,
    service: MessageServiceDep,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session_id: Annotated[str | None, Query()] = None,
) -> SuccessResponse[PaginatedData[MessageResponse]]:
    """Full-text search over message content, ranked by relevance."""
    messages, total = service.search_messages(q, limit=limit, offset=offset, session_id=session_id)
    page: PaginatedData[MessageResponse] = PaginatedData(
        items=[_to_response(m) for m in messages],
        total=total,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=page)


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[PaginatedData[MessageResponse]],
)
@limiter.limit(default_limit())
def list_messages(
    request: Request,
    session_id: str,
    service: MessageServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    sender: Annotated[str | None, Query()] = None,
) -> SuccessResponse[PaginatedData[MessageResponse]]:
    """Return a paginated list of a session's messages."""
    messages, total = service.list_session_messages(
        session_id, limit=limit, offset=offset, sender=sender
    )
    page: PaginatedData[MessageResponse] = PaginatedData(
        items=[_to_response(m) for m in messages],
        total=total,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=page)
