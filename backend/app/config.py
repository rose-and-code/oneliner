import os

from pydantic_settings import BaseSettings

ENV = os.getenv("ENV", "dev")


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "oneliner"
    jwt_secret: str
    jwt_expire_days: int = 7
    wechat_appid: str = ""
    wechat_secret: str = ""
    ark_api_key: str = ""
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_chat_model: str = "deepseek-v3-2-251201"
    llm_provider: str = "ark"
    openclaw_api_key: str = ""
    openclaw_base_url: str = "https://54.193.218.157/v1"
    openclaw_model: str = "openclaw"

    @property
    def database_url(self) -> str:
        return f"postgres://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = {"env_file": f".env.{ENV}", "env_file_encoding": "utf-8"}


settings = Settings()

TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": [
                "app.entities.user",
                "app.entities.favorite",
                "app.entities.event",
                "app.entities.sprout",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}
