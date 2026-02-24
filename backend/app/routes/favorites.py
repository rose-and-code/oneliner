from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.entities.user import User
from app.services.favorite import get_user_favorites
from app.services.favorite import toggle_favorite
from app.types.schemas import FavoriteListItem
from app.types.schemas import FavoriteResponse
from app.types.schemas import FavoriteToggleRequest
from app.types.schemas import PaginatedResponse
from app.utils.deps import current_user

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/toggle", response_model=FavoriteResponse)
async def toggle(req: FavoriteToggleRequest, user: CurrentUser):
    is_favorited = await toggle_favorite(user.id, req.sentence_id)
    return FavoriteResponse(is_favorited=is_favorited)


@router.get("/list", response_model=PaginatedResponse[FavoriteListItem])
async def list_favorites(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    user: CurrentUser = ...,
):
    return await get_user_favorites(user.id, page, page_size)
