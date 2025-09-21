from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    database_url: str
    pghost: Optional[str] = None
    pgdatabase: Optional[str] = None
    pguser: Optional[str] = None
    pgpassword: Optional[str] = None
    pgsslmode: Optional[str] = None
    pgchannelbinding: Optional[str] = None

    # Auth settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields

settings = Settings()