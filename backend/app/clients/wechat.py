import aiohttp


class WechatClient:
    """微信小程序 API 客户端"""

    BASE_URL = "https://api.weixin.qq.com"

    def __init__(self, appid: str, secret: str):
        self.appid = appid
        self.secret = secret

    async def code2session(self, code: str) -> str:
        """code 换 openid，失败抛 ValueError。"""
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                f"{self.BASE_URL}/sns/jscode2session",
                params={
                    "appid": self.appid,
                    "secret": self.secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            ) as resp,
        ):
            data = await resp.json()
        openid = data.get("openid")
        if not openid:
            raise ValueError(f"微信登录失败: {data.get('errmsg', '未知错误')}")
        return openid
