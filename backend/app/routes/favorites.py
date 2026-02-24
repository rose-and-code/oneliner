from fastapi import APIRouter, Depends, Query

from app.entities.user import User
from app.services.favorite import get_user_favorites, toggle_favorite
from app.types.schemas import FavoriteListItem, FavoriteResponse, FavoriteToggleRequest, PaginatedResponse
from app.utils.deps import current_user

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/toggle", response_model=FavoriteResponse)
async def toggle(req: FavoriteToggleRequest, user: User = Depends(current_user)):
    is_favorited = await toggle_favorite(user.id, req.sentence_id)
    return FavoriteResponse(is_favorited=is_favorited)


@router.get("/list", response_model=PaginatedResponse[FavoriteListItem])
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
):
    return await get_user_favorites(user.id, page, page_size)
