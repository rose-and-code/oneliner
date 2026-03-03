import os

from pydantic_settings import BaseSettings

ENV = os.getenv("ENV", "dev")


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_days: int = 7
    wechat_appid: str = ""
    wechat_secret: str = ""

    model_config = {"env_file": f".env.{ENV}", "env_file_encoding": "utf-8"}


settings = Settings()

TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["app.entities.user", "app.entities.favorite", "app.entities.event", "app.entities.sprout", "app.entities.agent_reply", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}
