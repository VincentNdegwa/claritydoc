from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    DATABASE_URL: str = ""
    DB_ECHO: bool = False

    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-4o"
    AI_API_KEY: str = ""
    
    AI_PRICING_INPUT: float = 5.0
    AI_PRICING_OUTPUT: float = 15.0
    
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    CLERK_SECRET_KEY: str = ""
    CLERK_JWT_KEY: str = ""
    CLERK_AUTHORIZED_PARTIES: list[str] = []
    CLERK_WEBHOOK_SIGNING_SECRET: str = ""

    STORAGE_PROVIDER: str = "local"
    STORAGE_BUCKET_NAME: Optional[str] = None

    STORAGE_AWS_ACCESS_KEY_ID: Optional[str] = None
    STORAGE_AWS_SECRET_ACCESS_KEY: Optional[str] = None
    STORAGE_AWS_REGION: Optional[str] = None

    STORAGE_DO_ACCESS_KEY_ID: Optional[str] = None
    STORAGE_DO_SECRET_ACCESS_KEY: Optional[str] = None
    STORAGE_DO_REGION: Optional[str] = None

    STORAGE_LOCAL_BASE_DIR: str = "storage_vault"

    REDIS_URL: str = "redis://localhost:6379"

    ENVIRONMENT: str = "development"


settings = Settings()
