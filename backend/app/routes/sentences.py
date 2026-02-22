from fastapi import APIRouter, Depends

from app.entities.user import User
from app.services.sentence import get_all_books_with_sentences
from app.types.schemas import BookWithSentencesResponse
from app.utils.deps import optional_user

router = APIRouter(prefix="/api/sentences", tags=["sentences"])


@router.get("/all", response_model=list[BookWithSentencesResponse])
async def get_all(user: User | None = Depends(optional_user)):
    user_id = user.id if user else None
    return await get_all_books_with_sentences(user_id)
