from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare Data Operations Platform"
    ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/healthcare_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "supersecretjwtkeychangeinproduction12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
