from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ia_crm"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = ""


settings = Settings()
