from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.entities.user import User
from app.services.book import get_all_books_with_sentences
from app.services.favorite import get_favorited_sentence_ids
from app.types.schemas import BookWithSentencesResponse
from app.types.schemas import PaginatedResponse
from app.utils.deps import optional_user

router = APIRouter(prefix="/api/books", tags=["books"])

OptionalUser = Annotated[User | None, Depends(optional_user)]


@router.get("/all", response_model=PaginatedResponse[BookWithSentencesResponse])
async def get_all(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    user: OptionalUser = None,
):
    favorited_ids: set[str] = set()
    if user:
        favorited_ids = await get_favorited_sentence_ids(user.id)
    return get_all_books_with_sentences(favorited_ids, page, page_size)
