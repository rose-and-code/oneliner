from uuid import UUID

from app.entities.favorite import Favorite
from app.services.book import get_sentence_by_id
from app.types.schemas import FavoriteListItem
from app.types.schemas import PaginatedResponse


async def toggle_favorite(user_id: UUID, sentence_id: UUID) -> bool:
    """切换收藏状态，返回当前是否已收藏。"""
    existing = await Favorite.filter(user_id=user_id, sentence_id=sentence_id).first()
    if existing:
        existing.is_cancelled = not existing.is_cancelled
        await existing.save()
        return not existing.is_cancelled

    await Favorite.create(user_id=user_id, sentence_id=sentence_id)
    return True


async def get_favorited_sentence_ids(user_id: UUID) -> set[str]:
    """获取用户所有已收藏的 sentence_id 集合。"""
    ids = await Favorite.filter(user_id=user_id, is_cancelled=False).values_list(
        "sentence_id", flat=True
    )
    return {str(sid) for sid in ids}


async def get_user_favorites(
    user_id: UUID, page: int = 1, page_size: int = 20
) -> PaginatedResponse[FavoriteListItem]:
    """获取用户收藏列表（分页）。"""
    total = await Favorite.filter(user_id=user_id, is_cancelled=False).count()
    offset = (page - 1) * page_size
    favorites = (
        await Favorite.filter(user_id=user_id, is_cancelled=False)
        .order_by("-created_at")
        .offset(offset)
        .limit(page_size)
    )

    items = []
    for fav in favorites:
        sentence = get_sentence_by_id(str(fav.sentence_id))
        book_title = ""
        book_author = ""
        if sentence:
            from app.services.book import _books
            for b in _books:
                if b["id"] == sentence.get("book_id"):
                    book_title = b["title"]
                    book_author = b["author"]
                    break
        items.append(
            FavoriteListItem(
                id=fav.id,
                sentence_id=fav.sentence_id,
                text=sentence["text"] if sentence else "",
                context_before=sentence.get("context_before", "") if sentence else "",
                context_after=sentence.get("context_after", "") if sentence else "",
                book_title=book_title,
                book_author=book_author,
                chapter=sentence.get("chapter", "") if sentence else "",
                themes=sentence.get("themes", []) if sentence else [],
                created_at=fav.created_at,
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )
