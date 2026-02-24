from fastapi import APIRouter, Depends, HTTPException

from app.entities.user import User
from app.services.auth import wechat_login
from app.types.schemas import TokenResponse, UpdateProfileRequest, UserResponse, WechatLoginRequest
from app.utils.deps import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: WechatLoginRequest):
    try:
        token, user = await wechat_login(req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="微信登录失败") from e
    return TokenResponse(token=token, user_id=user.id)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return UserResponse(id=user.id, nickname=user.nickname, avatar_url=user.avatar_url)


@router.post("/me/update", response_model=UserResponse)
async def update_me(req: UpdateProfileRequest, user: User = Depends(current_user)):
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    await user.save()
    return UserResponse(id=user.id, nickname=user.nickname, avatar_url=user.avatar_url)
