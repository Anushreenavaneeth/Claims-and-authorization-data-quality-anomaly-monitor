from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare Data Operations Platform"
    ENV: str = "development"
    DEBUG: bool = True

    # Database — switch from local to AWS RDS by changing this env var only
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/healthcare_db"

    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    # SMTP Email configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "notifications@healthdata-ops.internal"
    SMTP_FROM_NAME: str = "Healthcare DQ Monitor"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # Look for .env in current dir (backend/) then parent dir (project root)
    model_config = {"env_file": (".env", "../.env"), "case_sensitive": True, "extra": "ignore"}


settings = Settings()

