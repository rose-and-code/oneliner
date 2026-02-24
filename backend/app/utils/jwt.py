from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings


def create_token(user_id: str) -> str:
    """生成 JWT token。"""
    payload = {
        "sub": user_id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    """解码 JWT token，返回 user_id；token 无效或过期返回 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
