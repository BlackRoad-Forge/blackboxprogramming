try:
    from pydantic import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings

from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    app_name: str = "BlackboxProgramming"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str
    allowed_hosts: List[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
