from tortoise import fields

from app.entities.base import BaseEntity


class Sprout(BaseEntity):
    """冒芽：花灵主动生成的一句观察"""

    user_id = fields.UUIDField(index=True)
    text = fields.CharField(max_length=200)
    target_sentence_id = fields.UUIDField(null=True)
    shown = fields.BooleanField(default=False)

    class Meta:
        table = "sprout"
        ordering = ["-created_at"]
