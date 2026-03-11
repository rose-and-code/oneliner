from typing import ClassVar

from tortoise import fields

from app.entities.base import BaseEntity


class UserEvent(BaseEntity):
    """用户行为事件：停留、展开上下文、翻面等"""

    user_id = fields.UUIDField(index=True)
    event_type = fields.CharField(max_length=32, index=True)
    sentence_id = fields.UUIDField(null=True)
    book_id = fields.UUIDField(null=True)
    duration_ms = fields.IntField(null=True)
    meta = fields.JSONField(default=dict)

    class Meta:
        table = "user_event"
        ordering: ClassVar[list[str]] = ["-created_at"]
