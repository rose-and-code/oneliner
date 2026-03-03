from tortoise import fields

from app.entities.base import BaseEntity


class AgentReply(BaseEntity):
    user_id = fields.UUIDField(index=True)
    hook = fields.CharField(max_length=100)
    body = fields.TextField()
    target_sentence_id = fields.UUIDField(null=True)
    reaction_options = fields.JSONField(default=list)
    reaction = fields.CharField(max_length=20, null=True)
    shown = fields.BooleanField(default=False)

    class Meta:
        table = "agent_reply"
        ordering = ["-created_at"]
