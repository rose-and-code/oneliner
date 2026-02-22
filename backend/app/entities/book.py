from uuid import uuid4

from tortoise import fields
from tortoise.models import Model


class Book(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=128, index=True)
    author = fields.CharField(max_length=64)
    sentence_count = fields.IntField(default=0)
    sort_order = fields.IntField(default=0, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "books"
