"""Message endpoints.

Thin controllers: they translate HTTP to service calls and back. All business
logic lives in the service and pipeline; validation lives in the schemas.
"""

from typing import Annotated, cast

from fastapi import APIRouter, Query, status

from app.api.deps import MessageServiceDep
from app.models.message import Message
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.message import MessageCreate, MessageMetadata, MessageResponse, Sender

router = APIRouter(prefix="/api/messages", tags=["messages"])


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
def create_message(
    payload: MessageCreate,
    service: MessageServiceDep,
) -> SuccessResponse[MessageResponse]:
    """Validate, process and store an incoming chat message."""
    message = service.create_message(payload)
    return SuccessResponse(data=_to_response(message))


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[PaginatedData[MessageResponse]],
)
def list_messages(
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


