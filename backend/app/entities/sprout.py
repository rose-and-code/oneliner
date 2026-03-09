from tortoise import fields

from app.entities.base import BaseEntity


class Sprout(BaseEntity):
    user_id = fields.UUIDField(index=True)
    text = fields.CharField(max_length=500)
    hook = fields.CharField(max_length=100, default="")
    target_sentence_id = fields.UUIDField(null=True)
    reaction_options = fields.JSONField(default=list)
    reaction = fields.CharField(max_length=20, null=True)
    shown = fields.BooleanField(default=False)
    rec = fields.JSONField(default=None, null=True)

    class Meta:
        table = "sprout"
        ordering = ["-created_at"]
