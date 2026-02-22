import httpx

from app.config import settings
from app.entities.user import User
from app.utils.jwt import create_token

DEV_OPENID = "dev_openid_for_local_testing"


async def wechat_login(code: str) -> tuple[str, User]:
    """微信登录：code 换 openid，自动注册"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
    data = resp.json()
    openid = data.get("openid")
    if not openid:
        raise ValueError(f"微信登录失败: {data.get('errmsg', '未知错误')}")

    return await _get_or_create_user(openid)


async def dev_login() -> tuple[str, User]:
    """开发模式登录：跳过微信 code 校验，直接创建/获取测试用户"""
    return await _get_or_create_user(DEV_OPENID)


async def _get_or_create_user(openid: str) -> tuple[str, User]:
    """根据 openid 获取或创建用户，返回 token 和用户"""
    user = await User.filter(openid=openid).first()
    if not user:
        user = await User.create(openid=openid, nickname="开发者")

    token = create_token(str(user.id))
    return token, user
