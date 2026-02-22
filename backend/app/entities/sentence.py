from uuid import uuid4

from tortoise import fields
from tortoise.models import Model


class Sentence(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    book_id = fields.UUIDField(index=True)
    text = fields.TextField()
    context_before = fields.TextField(default="")
    context_after = fields.TextField(default="")
    chapter = fields.CharField(max_length=256, default="")
    ai_explanation = fields.TextField(default="")
    counter_quote = fields.TextField(default="")
    counter_source = fields.CharField(max_length=256, default="")
    similar_quotes = fields.JSONField(default=list)
    opposite_quotes = fields.JSONField(default=list)
    sort_order = fields.IntField(default=0, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sentences"
