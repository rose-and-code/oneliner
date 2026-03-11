from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from loguru import logger
from pydantic import BaseModel

from app.entities.event import UserEvent
from app.entities.user import User
from app.services.agent import analyze_events_and_generate_reply
from app.services.garden import create_sprout
from app.services.garden import get_user_context
from app.services.garden import should_generate_sprout_on_event
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


async def _try_generate_sprout_from_events(user_id: UUID):
    """后台任务：分析行为事件，尝试生成冒芽"""
    logger.info("开始尝试生成冒芽 user={}", user_id)
    if not should_generate_sprout_on_event(user_id):
        logger.info("冷却未到，跳过")  # noqa: RUF001
        return
    ctx = await get_user_context(user_id)
    logger.info("调用 LLM...")
    result = await analyze_events_and_generate_reply(user_id, ctx)
    if not result:
        logger.warning("LLM 返回空")
        return
    await create_sprout(
        user_id,
        text=result.get("body", result.get("text", "")),
        hook=result.get("hook", ""),
        target_sentence_id=result.get("target_sentence_id"),
        reaction_options=result.get("reaction_options"),
        rec=result.get("rec"),
    )
    logger.info("冒芽生成成功: {}", result.get("hook", "")[:30])


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
    bg.add_task(_try_generate_sprout_from_events, user.id)
    return {"created": len(objs)}
