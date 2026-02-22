from uuid import UUID

from pydantic import BaseModel


class WechatLoginRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str
    user_id: str


class UserResponse(BaseModel):
    id: str
    nickname: str
    avatar_url: str


class UpdateProfileRequest(BaseModel):
    nickname: str
    avatar_url: str


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    sentence_count: int
    sort_order: int


class RelatedQuote(BaseModel):
    text: str
    book_title: str
    book_author: str
    sentence_id: str | None = None


class SentenceResponse(BaseModel):
    id: str
    book_id: str
    text: str
    context_before: str
    context_after: str
    chapter: str
    ai_explanation: str
    counter_quote: str
    counter_source: str
    similar_quotes: list[RelatedQuote] = []
    opposite_quotes: list[RelatedQuote] = []
    sort_order: int
    is_bookmarked: bool = False


class BookWithSentencesResponse(BaseModel):
    book: BookResponse
    sentences: list[SentenceResponse]


class BookmarkToggleRequest(BaseModel):
    sentence_id: UUID


class BookmarkResponse(BaseModel):
    is_bookmarked: bool


class BookmarkListItem(BaseModel):
    id: str
    sentence_id: str
    text: str
    context_before: str
    context_after: str
    book_title: str
    book_author: str
    chapter: str
    similar_quotes: list[RelatedQuote] = []
    opposite_quotes: list[RelatedQuote] = []
    created_at: str
