"""Service Schema テスト"""
import pytest
from datetime import datetime

from app.schemas.service import ServiceResponse, ServiceListResponse


class Test正常系:
    """正常系テスト"""
    
    def test_should_create_service_response_with_valid_data(self, test_service_file):
        """ServiceResponseが有効なデータで作成できる"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        
        # Act
        response = ServiceResponse(
            id=service.id,
            name=service.name,
            description=service.description,
            version=service.version,
            base_url=service.base_url,
            role_endpoint=service.role_endpoint,
            health_endpoint=service.health_endpoint,
            is_active=service.is_active,
            metadata=service.metadata,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
        
        # Assert
        assert response.id == "file-service"
        assert response.name == "ファイル管理サービス"
    
    def test_should_create_service_list_response_with_valid_data(self, test_service_file):
        """ServiceListResponseが有効なデータで作成できる"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        
        response_item = ServiceResponse(
            id=service.id,
            name=service.name,
            description=service.description,
            version=service.version,
            base_url=service.base_url,
            role_endpoint=service.role_endpoint,
            health_endpoint=service.health_endpoint,
            is_active=service.is_active,
            metadata=service.metadata,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
        
        # Act
        response = ServiceListResponse(
            data=[response_item]
        )
        
        # Assert
        assert len(response.data) == 1
        assert response.data[0].id == "file-service"
    
    def test_should_serialize_to_json_correctly(self, test_service_file):
        """ServiceResponseが正しくJSONシリアライズできる"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        response = ServiceResponse(
            id=service.id,
            name=service.name,
            description=service.description,
            version=service.version,
            base_url=service.base_url,
            role_endpoint=service.role_endpoint,
            health_endpoint=service.health_endpoint,
            is_active=service.is_active,
            metadata=service.metadata,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
        
        # Act
        json_data = response.model_dump(mode="json")
        
        # Assert
        assert json_data["id"] == "file-service"
        assert "created_at" in json_data
