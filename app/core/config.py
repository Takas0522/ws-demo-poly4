from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server Configuration
    PORT: int = 3003
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"

    # CosmosDB Configuration
    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DATABASE: str = "settingsdb"
    COSMOS_CONTAINER: str = "configurations"

    # JWT Configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "auth-service"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
