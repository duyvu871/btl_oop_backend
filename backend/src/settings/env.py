
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email settings (if using)
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for creating links

    # ARQ Worker settings
    ARQ_QUEUE_NAME: str = "arq:queue"
    ARQ_MAX_JOBS: int = 10
    ARQ_JOB_TIMEOUT: int = 600  # 10 minutes

    # Sentry settings
    SENTRY_DSN: str | None = None

    # Other settings
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    def validate_smtp_config(self) -> bool:
        """Check if SMTP is properly configured"""
        return all([
            self.SMTP_HOST,
            self.SMTP_PORT,
            self.SMTP_USER,
            self.SMTP_PASSWORD,
            self.EMAILS_FROM_EMAIL
        ])


# Create an instance of Settings to use throughout the application
settings = Settings()
