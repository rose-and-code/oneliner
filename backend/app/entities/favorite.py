from tortoise import fields

from app.entities.base import BaseEntity


class Favorite(BaseEntity):
    user_id = fields.UUIDField(index=True)
    sentence_id = fields.UUIDField(index=True)
    is_cancelled = fields.BooleanField(default=False)

    class Meta:
        table = "favorites"
        unique_together = (("user_id", "sentence_id"),)
