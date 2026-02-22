from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgres://rosewei@localhost:5432/oneliner"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_expire_days: int = 7
    wechat_appid: str = ""
    wechat_secret: str = ""
    dev_mode: bool = True

    model_config = {"env_file": ".env.dev", "env_file_encoding": "utf-8"}


settings = Settings()

TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["app.entities.user", "app.entities.book", "app.entities.sentence", "app.entities.bookmark", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}
