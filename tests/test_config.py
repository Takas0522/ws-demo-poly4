"""config テスト"""
import pytest
import os
from app.config import Settings


class Test正常系:
    """正常系テスト"""
    
    def test_should_load_default_settings(self):
        """デフォルト設定が読み込まれる"""
        # Arrange & Act
        settings = Settings()
        
        # Assert
        assert settings.SERVICE_NAME == "service-setting-service"
        assert settings.API_VERSION == "v1"
        assert settings.ENVIRONMENT in ["development", "test", "staging", "production"]
    
    def test_should_detect_non_production_environment(self):
        """非本番環境を検出する"""
        # Arrange
        original_env = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "development"
        
        # Act
        settings = Settings()
        
        # Assert
        assert settings.is_production is False
        
        # Cleanup
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            if "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]
