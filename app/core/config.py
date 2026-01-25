"""Application configuration settings."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = "Service Setting Service"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8004

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Cosmos DB Configuration
    cosmosdb_endpoint: str
    cosmosdb_key: str
    cosmosdb_database: str = "management-app"
    cosmosdb_services_container: str = "services"
    cosmosdb_service_assignments_container: str = "service-assignments"

    # Auth Service Configuration
    auth_service_url: str = "http://localhost:8003"
    auth_service_public_key_endpoint: str = "/api/auth/public-key"

    # JWT Configuration
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "management-app"
    jwt_issuer: str = "auth-service"

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"


# Global settings instance
settings = Settings()
