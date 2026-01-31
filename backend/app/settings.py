from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+asyncpg://ia_app:ia_app@localhost:5432/ia_crm"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = ""
    jwt_secret: str | None = None
    jwt_alg: str = "HS256"
    access_token_ttl_seconds: int = 3600
    bootstrap_token: str = ""

    def require_jwt_secret(self) -> str:
        if self.jwt_secret:
            return self.jwt_secret
        if self.environment in {"local", "dev"}:
            return "dev-jwt-secret-change-me"
        raise RuntimeError("JWT_SECRET is required outside local/dev environments")


settings = Settings()
