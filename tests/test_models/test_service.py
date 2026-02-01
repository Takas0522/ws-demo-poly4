"""Service Model テスト"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.service import Service


class Test正常系:
    """正常系テスト"""
    
    def test_should_create_service_with_valid_data(self, test_service_file):
        """MT_S001: 有効なServiceモデルが作成できる"""
        # Arrange
        # Act
        service = Service(**test_service_file)
        
        # Assert
        assert service.id == "file-service"
        assert service.name == "ファイル管理サービス"
        assert service.is_active is True
    
    def test_should_set_default_values_correctly(self):
        """MT_S002: デフォルト値が正しく設定される"""
        # Arrange
        # Act
        service = Service(
            id="test-service",
            tenant_id="_system",
            name="Test Service",
            version="1.0.0"
        )
        
        # Assert
        assert service.is_active is True
        assert service.metadata == {}
    
    def test_should_accept_nested_metadata(self):
        """MT_S007: metadataにネストオブジェクトを含められる"""
        # Arrange
        nested_metadata = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        # Act
        service = Service(
            id="test-service",
            tenant_id="_system",
            name="Test Service",
            version="1.0.0",
            metadata=nested_metadata
        )
        
        # Assert
        assert service.metadata["level1"]["level2"]["level3"] == "value"


class Test異常系:
    """異常系テスト"""
    
    def test_should_raise_validation_error_when_id_is_empty(self):
        """MT_S003: service_idが空文字列でバリデーションエラー"""
        # Arrange
        # Act & Assert
        with pytest.raises(ValidationError):
            Service(
                id="",
                tenant_id="_system",
                name="Test Service",
                version="1.0.0"
            )
    
    def test_should_raise_validation_error_when_id_has_invalid_format(self):
        """MT_S004: service_idが不正な形式でエラー"""
        # Arrange
        # Act & Assert
        with pytest.raises(ValidationError):
            Service(
                id="Invalid_ID_With_CAPS",
                tenant_id="_system",
                name="Test Service",
                version="1.0.0"
            )


class Test境界値:
    """境界値テスト"""
    
    def test_should_accept_id_with_100_characters(self):
        """MT_S005: service_idが100文字でOK"""
        # Arrange
        long_id = "a" * 100
        
        # Act
        service = Service(
            id=long_id,
            tenant_id="_system",
            name="Test Service",
            version="1.0.0"
        )
        
        # Assert
        assert len(service.id) == 100
    
    def test_should_raise_validation_error_when_id_exceeds_100_characters(self):
        """MT_S006: service_idが101文字でエラー"""
        # Arrange
        long_id = "a" * 101
        
        # Act & Assert
        with pytest.raises(ValidationError):
            Service(
                id=long_id,
                tenant_id="_system",
                name="Test Service",
                version="1.0.0"
            )
