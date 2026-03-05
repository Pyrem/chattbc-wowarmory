from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "chattbc"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://chattbc:chattbc_dev@localhost:5432/chattbc"

    @model_validator(mode="after")
    def _fix_database_url(self) -> "Settings":
        """Render provides postgres:// — asyncpg needs postgresql+asyncpg://."""
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Blizzard Developer API (Client Credentials)
    blizzard_client_id: str = ""
    blizzard_client_secret: str = ""
    blizzard_region: str = "us"

    # Blizzard OAuth (Authorization Code — for Battle.net linking)
    bnet_oauth_client_id: str = ""
    bnet_oauth_client_secret: str = ""
    bnet_oauth_redirect_uri: str = "http://localhost:8000/api/auth/bnet/callback"


settings = Settings()
