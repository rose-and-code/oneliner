from tortoise import fields

from app.entities.base import BaseEntity


class Sprout(BaseEntity):
    user_id = fields.UUIDField(index=True)
    text = fields.CharField(max_length=200)
    hook = fields.CharField(max_length=100, default="")
    target_sentence_id = fields.UUIDField(null=True)
    reaction_options = fields.JSONField(default=list)
    reaction = fields.CharField(max_length=20, null=True)
    shown = fields.BooleanField(default=False)

    class Meta:
        table = "sprout"
        ordering = ["-created_at"]
