from uuid import uuid4

from tortoise import fields
from tortoise.models import Model


class Bookmark(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    user_id = fields.UUIDField(index=True)
    sentence_id = fields.UUIDField(index=True)
    cancelled = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "bookmarks"
        unique_together = (("user_id", "sentence_id"),)
