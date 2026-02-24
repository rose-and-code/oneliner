from app.clients.wechat import WechatClient
from app.config import settings
from app.entities.user import User
from app.utils.jwt import create_token

wechat_client = WechatClient(settings.wechat_appid, settings.wechat_secret)


async def wechat_login(code: str) -> tuple[str, User]:
    """微信登录：code 换 openid，自动注册"""
    openid = await wechat_client.code2session(code)
    return await _get_or_create_user(openid)


async def _get_or_create_user(openid: str) -> tuple[str, User]:
    """根据 openid 获取或创建用户，返回 token 和用户"""
    user = await User.filter(openid=openid).first()
    if not user:
        user = await User.create(openid=openid)

    token = create_token(str(user.id))
    return token, user
