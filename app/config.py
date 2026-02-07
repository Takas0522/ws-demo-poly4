from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service settings
    service_name: str = "tenant-management-service"
    port: int = 8002

    # Cosmos DB settings
    cosmos_db_endpoint: str
    cosmos_db_key: str
    cosmos_db_database: str = "tenant_management"
    cosmos_db_container: str = "tenants"
    cosmos_db_connection_verify: bool = True

    # JWT settings
    jwt_secret: str = "your-development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000"]

    # 特権テナントID
    privileged_tenant_id: str = "privileged-tenant-001"

    # Log settings
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
