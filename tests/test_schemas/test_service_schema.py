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
        response = ServiceResponse.model_validate(service)
        
        # Assert
        assert response.id == "file-service"
        assert response.name == "ファイル管理サービス"
    
    def test_should_create_service_list_response_with_valid_data(self, test_service_file):
        """ServiceListResponseが有効なデータで作成できる"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        services = [service]
        
        # Act
        response = ServiceListResponse(
            data=[ServiceResponse.model_validate(s) for s in services]
        )
        
        # Assert
        assert len(response.data) == 1
        assert response.data[0].id == "file-service"
    
    def test_should_serialize_to_json_correctly(self, test_service_file):
        """ServiceResponseが正しくJSONシリアライズできる"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        response = ServiceResponse.model_validate(service)
        
        # Act
        json_data = response.model_dump(mode="json")
        
        # Assert
        assert json_data["id"] == "file-service"
        assert "createdAt" in json_data
