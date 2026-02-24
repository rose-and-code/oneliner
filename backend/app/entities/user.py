from tortoise import fields

from app.entities.base import BaseEntity


class User(BaseEntity):
    openid = fields.CharField(max_length=128, unique=True, index=True)
    nickname = fields.CharField(max_length=64, default="")
    avatar_url = fields.CharField(max_length=512, default="")

    class Meta:
        table = "users"
