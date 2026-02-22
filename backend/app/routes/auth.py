from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.entities.user import User
from app.services.auth import dev_login, wechat_login
from app.types.schemas import TokenResponse, UpdateProfileRequest, UserResponse, WechatLoginRequest
from app.utils.deps import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: WechatLoginRequest):
    try:
        token, user = await wechat_login(req.code)
    except ValueError:
        if not settings.dev_mode:
            raise HTTPException(status_code=400, detail="微信登录失败")
        print("微信登录失败，降级到开发模式登录")
        token, user = await dev_login()
    return TokenResponse(token=token, user_id=str(user.id))


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login_endpoint():
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail="仅开发环境可用")
    token, user = await dev_login()
    return TokenResponse(token=token, user_id=str(user.id))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return UserResponse(id=str(user.id), nickname=user.nickname, avatar_url=user.avatar_url)


@router.put("/me", response_model=UserResponse)
async def update_me(req: UpdateProfileRequest, user: User = Depends(current_user)):
    user.nickname = req.nickname
    user.avatar_url = req.avatar_url
    await user.save()
    return UserResponse(id=str(user.id), nickname=user.nickname, avatar_url=user.avatar_url)
