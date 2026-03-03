import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from pydantic import BaseModel

from app.entities.event import UserEvent
from app.entities.user import User
from app.services.agent import analyze_events_and_generate_reply
from app.services.garden import create_agent_reply
from app.services.garden import get_user_context
from app.services.garden import should_generate_reply
from app.utils.deps import current_user

logger = logging.getLogger(__name__)

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


async def _try_generate_reply(user_id):
    """后台任务：分析行为事件，尝试生成花灵回复"""
    await asyncio.sleep(2)
    if not await should_generate_reply(user_id):
        return
    ctx = await get_user_context(user_id)
    result = await analyze_events_and_generate_reply(user_id, ctx)
    if not result:
        return
    await create_agent_reply(
        user_id,
        hook=result["hook"],
        body=result["body"],
        target_sentence_id=result.get("target_sentence_id"),
        reaction_options=result.get("reaction_options"),
    )
    logger.info("花灵回复生成: %s", result["hook"][:30])


@router.post("/batch")
async def batch_create(req: BatchEventsRequest, user: CurrentUser, bg: BackgroundTasks):
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
    bg.add_task(_try_generate_reply, user.id)
    return {"created": len(objs)}
