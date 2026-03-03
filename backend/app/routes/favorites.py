import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Query

from app.entities.user import User
from app.services.agent import generate_sprout
from app.services.favorite import get_user_favorites
from app.services.favorite import toggle_favorite
from app.services.garden import create_sprout
from app.services.garden import get_notification_payload
from app.services.garden import get_user_context
from app.services.garden import should_generate_sprout
from app.types.schemas import FavoriteListItem
from app.types.schemas import FavoriteToggleRequest
from app.types.schemas import PaginatedResponse
from app.utils.deps import current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

CurrentUser = Annotated[User, Depends(current_user)]


async def _try_generate_sprout(user_id):
    """后台任务：尝试为用户生成冒芽"""
    await asyncio.sleep(1)
    if not await should_generate_sprout(user_id):
        return
    ctx = await get_user_context(user_id)
    result = await generate_sprout(ctx)
    if result and result.get("text"):
        await create_sprout(user_id, result["text"], result.get("target_sentence_id"))
        logger.info("冒芽生成成功: %s", result["text"][:30])


@router.post("/toggle")
async def toggle(req: FavoriteToggleRequest, user: CurrentUser, bg: BackgroundTasks):
    is_favorited = await toggle_favorite(user.id, req.sentence_id)
    if is_favorited:
        bg.add_task(_try_generate_sprout, user.id)
    notification = await get_notification_payload(user.id)
    return {"is_favorited": is_favorited, "_notification": notification}


@router.get("/list", response_model=PaginatedResponse[FavoriteListItem])
async def list_favorites(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    user: CurrentUser = ...,
):
    return await get_user_favorites(user.id, page, page_size)
