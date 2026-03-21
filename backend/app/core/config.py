from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Arcore SyncBridge"
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3005"
    ENABLE_TOKEN_DEBUG_ENDPOINT: bool = False
    AUTH_MODE: str = "disabled"
    AUTH_HEADER_EMAIL: str = "X-User-Email"
    AUTH_HEADER_ROLE: str = "X-User-Role"
    AUTH_DISABLED_ROLE: str = "platform_admin"
    AUTH_DEFAULT_ROLE: str = "viewer"
    AUTH_AUTO_PROVISION_USERS: bool = True

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
