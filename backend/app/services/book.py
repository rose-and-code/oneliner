import hashlib
import json
from pathlib import Path
from uuid import UUID

from app.types.schemas import BookResponse
from app.types.schemas import BookWithSentencesResponse
from app.types.schemas import PaginatedResponse
from app.types.schemas import RelatedQuote
from app.types.schemas import SentenceResponse

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "books.json"

_books: list[dict] = []
_sentence_index: dict[str, dict] = {}


def _stable_uuid(namespace: str, key: str) -> UUID:
    """基于 namespace + key 生成稳定的确定性 UUID。"""
    digest = hashlib.sha256(f"{namespace}:{key}".encode()).hexdigest()
    return UUID(digest[:32])


def load_books():
    """启动时加载 JSON 数据到内存。"""
    global _books, _sentence_index
    with Path(DATA_PATH).open(encoding="utf-8") as f:
        raw = json.load(f)

    _books = []
    _sentence_index = {}

    for book_data in sorted(raw, key=lambda b: b["sort_order"]):
        book_id = _stable_uuid("book", f"{book_data['title']}__{book_data['author']}")
        book = {**book_data, "id": book_id, "sentences": []}

        for s in sorted(book_data["sentences"], key=lambda x: x["sort_order"]):
            sentence_id = _stable_uuid("sentence", f"{book_id}|{s['text'][:50]}")
            sentence = {**s, "id": sentence_id, "book_id": book_id}
            book["sentences"].append(sentence)
            _sentence_index[str(sentence_id)] = sentence

        book["sentence_count"] = len(book["sentences"])
        _books.append(book)


def get_all_books_with_sentences(
    favorited_ids: set[str] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[BookWithSentencesResponse]:
    """返回分页的书籍及句子。"""
    favorited = favorited_ids or set()
    total = len(_books)
    start = (page - 1) * page_size
    end = start + page_size
    page_books = _books[start:end]

    items = [
        BookWithSentencesResponse(
            book=BookResponse(
                id=b["id"],
                title=b["title"],
                author=b["author"],
                sentence_count=b["sentence_count"],
                sort_order=b["sort_order"],
            ),
            sentences=[
                SentenceResponse(
                    id=s["id"],
                    book_id=s["book_id"],
                    text=s["text"],
                    context_before=s.get("context_before", ""),
                    context_after=s.get("context_after", ""),
                    chapter=s.get("chapter", ""),
                    similar_quotes=[
                        RelatedQuote(**q) for q in s.get("similar_quotes", [])
                    ],
                    opposite_quotes=[
                        RelatedQuote(**q) for q in s.get("opposite_quotes", [])
                    ],
                    sort_order=s["sort_order"],
                    is_favorited=str(s["id"]) in favorited,
                )
                for s in b["sentences"]
            ],
        )
        for b in page_books
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


def get_sentence_by_id(sentence_id: str) -> dict | None:
    """根据 ID 查找句子。"""
    return _sentence_index.get(sentence_id)
