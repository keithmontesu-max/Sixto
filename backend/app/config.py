"""Central settings — secrets come from environment only."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://sixto:change_me@localhost:5432/sixto"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "dev-only-change-me-min-32-chars-long!!"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    ENV: str = "dev"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
