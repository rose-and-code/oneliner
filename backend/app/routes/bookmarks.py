from fastapi import APIRouter, Depends

from app.entities.user import User
from app.services.bookmark import get_user_bookmarks, toggle_bookmark
from app.types.schemas import BookmarkListItem, BookmarkResponse, BookmarkToggleRequest
from app.utils.deps import current_user

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.post("/toggle", response_model=BookmarkResponse)
async def toggle(req: BookmarkToggleRequest, user: User = Depends(current_user)):
    is_bookmarked = await toggle_bookmark(user.id, req.sentence_id)
    return BookmarkResponse(is_bookmarked=is_bookmarked)


@router.get("/list", response_model=list[BookmarkListItem])
async def list_bookmarks(user: User = Depends(current_user)):
    return await get_user_bookmarks(user.id)
