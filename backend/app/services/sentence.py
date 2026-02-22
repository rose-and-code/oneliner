from uuid import UUID

from app.entities.book import Book
from app.entities.bookmark import Bookmark
from app.entities.sentence import Sentence
from app.types.schemas import BookResponse, BookWithSentencesResponse, RelatedQuote, SentenceResponse


async def get_all_books_with_sentences(user_id: UUID | None = None) -> list[BookWithSentencesResponse]:
    """获取所有书籍及其句子，按 sort_order 排序"""
    books = await Book.all().order_by("sort_order")
    bookmarked_ids: set[str] = set()
    if user_id:
        bookmarks = await Bookmark.filter(user_id=user_id, cancelled=False).values_list("sentence_id", flat=True)
        bookmarked_ids = {str(sid) for sid in bookmarks}

    result = []
    for book in books:
        sentences = await Sentence.filter(book_id=book.id).order_by("sort_order")
        result.append(
            BookWithSentencesResponse(
                book=BookResponse(
                    id=str(book.id),
                    title=book.title,
                    author=book.author,
                    sentence_count=book.sentence_count,
                    sort_order=book.sort_order,
                ),
                sentences=[
                    SentenceResponse(
                        id=str(s.id),
                        book_id=str(s.book_id),
                        text=s.text,
                        context_before=s.context_before,
                        context_after=s.context_after,
                        chapter=s.chapter,
                        ai_explanation=s.ai_explanation,
                        counter_quote=s.counter_quote,
                        counter_source=s.counter_source,
                        similar_quotes=[RelatedQuote(**q) for q in (s.similar_quotes or [])],
                        opposite_quotes=[RelatedQuote(**q) for q in (s.opposite_quotes or [])],
                        sort_order=s.sort_order,
                        is_bookmarked=str(s.id) in bookmarked_ids,
                    )
                    for s in sentences
                ],
            )
        )
    return result
