from datetime import datetime
from typing import Generic
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from pydantic import field_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool


class WechatLoginRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str
    user_id: UUID


class UserResponse(BaseModel):
    id: UUID
    nickname: str
    avatar_url: str


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str | None) -> str | None:
        if v is not None and (len(v.strip()) == 0 or len(v) > 64):
            raise ValueError("昵称长度 1-64 字符")
        return v


class RelatedQuote(BaseModel):
    text: str
    book_title: str
    book_author: str
    sentence_id: UUID | None = None


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    sentence_count: int
    sort_order: int


class SentenceResponse(BaseModel):
    id: UUID
    book_id: UUID
    text: str
    context_before: str
    context_after: str
    chapter: str
    similar_quotes: list[RelatedQuote] = []
    opposite_quotes: list[RelatedQuote] = []
    sort_order: int
    is_favorited: bool = False
    themes: list[str] = []


class BookWithSentencesResponse(BaseModel):
    book: BookResponse
    sentences: list[SentenceResponse]


class FavoriteToggleRequest(BaseModel):
    sentence_id: UUID


class FavoriteResponse(BaseModel):
    is_favorited: bool


class FavoriteListItem(BaseModel):
    id: UUID
    sentence_id: UUID
    text: str = ""
    context_before: str = ""
    context_after: str = ""
    book_title: str = ""
    book_author: str = ""
    chapter: str = ""
    themes: list[str] = []
    created_at: datetime


class SproutResponse(BaseModel):
    id: UUID
    text: str
    hook: str = ""
    target_sentence_id: UUID | None = None
    reaction_options: list[str] = []
    reaction: str | None = None
    created_at: datetime


class SproutListResponse(BaseModel):
    items: list[SproutResponse]


class ReactionRequest(BaseModel):
    reaction: str

    @field_validator("reaction")
    @classmethod
    def validate_reaction(cls, v: str) -> str:
        if not v or len(v.strip()) == 0 or len(v) > 20:
            raise ValueError("回应内容 1-20 字符")
        return v.strip()
