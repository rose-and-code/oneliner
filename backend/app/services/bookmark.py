from uuid import UUID

from app.entities.book import Book
from app.entities.bookmark import Bookmark
from app.entities.sentence import Sentence
from app.types.schemas import BookmarkListItem, RelatedQuote


async def toggle_bookmark(user_id: UUID, sentence_id: UUID) -> bool:
    """切换收藏状态，返回当前是否已收藏"""
    existing = await Bookmark.filter(user_id=user_id, sentence_id=sentence_id).first()
    if existing:
        existing.cancelled = not existing.cancelled
        await existing.save()
        return not existing.cancelled

    await Bookmark.create(user_id=user_id, sentence_id=sentence_id)
    return True


def _build_related_quotes(raw: list) -> list[RelatedQuote]:
    """将 JSON 字段中的原始数据转换为 RelatedQuote 列表"""
    return [RelatedQuote(**q) for q in raw] if raw else []


async def get_user_bookmarks(user_id: UUID) -> list[BookmarkListItem]:
    """获取用户收藏列表"""
    bookmarks = await Bookmark.filter(user_id=user_id, cancelled=False).order_by("-created_at")
    result = []
    for bm in bookmarks:
        sentence = await Sentence.filter(id=bm.sentence_id).first()
        if not sentence:
            continue
        book = await Book.filter(id=sentence.book_id).first()
        if not book:
            continue
        result.append(
            BookmarkListItem(
                id=str(bm.id),
                sentence_id=str(sentence.id),
                text=sentence.text,
                context_before=sentence.context_before,
                context_after=sentence.context_after,
                book_title=book.title,
                book_author=book.author,
                chapter=sentence.chapter,
                similar_quotes=_build_related_quotes(sentence.similar_quotes),
                opposite_quotes=_build_related_quotes(sentence.opposite_quotes),
                created_at=bm.created_at.isoformat(),
            )
        )
    return result
