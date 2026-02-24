from fastapi import APIRouter, Depends, Query

from app.entities.user import User
from app.services.book import get_all_books_with_sentences
from app.services.favorite import get_favorited_sentence_ids
from app.types.schemas import BookWithSentencesResponse, PaginatedResponse
from app.utils.deps import optional_user

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/all", response_model=PaginatedResponse[BookWithSentencesResponse])
async def get_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User | None = Depends(optional_user),
):
    favorited_ids: set[str] = set()
    if user:
        favorited_ids = await get_favorited_sentence_ids(user.id)
    return get_all_books_with_sentences(favorited_ids, page, page_size)
