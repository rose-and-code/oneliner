from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.entities.user import User
from app.services.auth import wechat_login
from app.types.schemas import TokenResponse
from app.types.schemas import UpdateProfileRequest
from app.types.schemas import UserResponse
from app.types.schemas import WechatLoginRequest
from app.utils.deps import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/login", response_model=TokenResponse)
async def login(req: WechatLoginRequest):
    try:
        token, user = await wechat_login(req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="微信登录失败") from e
    return TokenResponse(token=token, user_id=user.id)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser):
    return UserResponse(id=user.id, nickname=user.nickname, avatar_url=user.avatar_url)


@router.post("/me/update", response_model=UserResponse)
async def update_me(req: UpdateProfileRequest, user: CurrentUser):
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    await user.save()
    return UserResponse(id=user.id, nickname=user.nickname, avatar_url=user.avatar_url)
