from uuid import uuid4

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    openid = fields.CharField(max_length=128, unique=True, index=True)
    nickname = fields.CharField(max_length=64, default="")
    avatar_url = fields.CharField(max_length=512, default="")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
