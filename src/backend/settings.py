from typing import List
import os


class Settings:
    """
    Application settings loaded from environment variables.
    """

    app_name: str = "BlackboxProgramming"
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = os.getenv("DATABASE_URL", "")
    allowed_hosts: List[str] = ["*"]


settings = Settings()
