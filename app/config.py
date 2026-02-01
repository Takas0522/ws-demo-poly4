"""アプリケーション設定"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定クラス"""

    # アプリケーション設定
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "service-setting-service")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_VERSION: str = os.getenv("API_VERSION", "v1")

    # Cosmos DB設定
    COSMOS_DB_CONNECTION_STRING: str = os.getenv("COSMOS_DB_CONNECTION_STRING", "")
    COSMOS_DB_DATABASE_NAME: str = os.getenv("COSMOS_DB_DATABASE_NAME", "management-app")
    COSMOS_DB_CONTAINER_NAME: str = os.getenv("COSMOS_DB_CONTAINER_NAME", "service_setting")

    # JWT設定
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Application Insights
    APPINSIGHTS_INSTRUMENTATIONKEY: str = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY", "")

    # CORS設定
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")

    # 外部サービス設定
    TENANT_SERVICE_BASE_URL: str = os.getenv(
        "TENANT_SERVICE_BASE_URL", "http://localhost:8001"
    )

    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.ENVIRONMENT == "development"

    def validate(self) -> None:
        """必須設定の検証"""
        errors = []

        if not self.COSMOS_DB_CONNECTION_STRING:
            errors.append("COSMOS_DB_CONNECTION_STRING is required")

        if not self.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY is required")
        elif len(self.JWT_SECRET_KEY) < 64:
            errors.append("JWT_SECRET_KEY must be at least 64 characters")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


settings = Settings()
