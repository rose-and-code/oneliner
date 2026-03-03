from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel

from app.entities.event import UserEvent
from app.entities.user import User
from app.utils.deps import current_user

router = APIRouter(prefix="/api/events", tags=["events"])

CurrentUser = Annotated[User, Depends(current_user)]


class EventItem(BaseModel):
    event_type: str
    sentence_id: str = ""
    book_id: str = ""
    duration_ms: int = 0
    meta: dict = {}


class BatchEventsRequest(BaseModel):
    events: list[EventItem]


@router.post("/batch")
async def batch_create(req: BatchEventsRequest, user: CurrentUser):
    """批量写入用户行为事件"""
    objs = [
        UserEvent(
            user_id=user.id,
            event_type=e.event_type,
            sentence_id=e.sentence_id or None,
            book_id=e.book_id or None,
            duration_ms=e.duration_ms or None,
            meta=e.meta,
        )
        for e in req.events
    ]
    await UserEvent.bulk_create(objs)
    return {"created": len(objs)}
