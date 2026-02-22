from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.entities.user import User
from app.utils.jwt import decode_token

bearer_scheme = HTTPBearer()


async def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> User:
    """必须登录的依赖"""
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")
    user = await User.filter(id=UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))) -> User | None:
    """可选登录的依赖"""
    if not credentials:
        return None
    user_id = decode_token(credentials.credentials)
    if not user_id:
        return None
    return await User.filter(id=UUID(user_id)).first()
