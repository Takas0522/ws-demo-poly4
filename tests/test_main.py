"""main テスト"""
import pytest


class Test正常系:
    """正常系テスト"""
    
    def test_should_return_404_for_unknown_endpoint(self):
        """存在しないエンドポイントで404を返す"""
        # Arrange
        from fastapi.testclient import TestClient
        from app.main import app
        from app.dependencies import get_cosmos_container
        from unittest.mock import MagicMock
        
        # Mock cosmos container
        mock_container = MagicMock()
        app.dependency_overrides[get_cosmos_container] = lambda: mock_container
        
        client = TestClient(app)
        
        # Act
        response = client.get("/unknown")
        
        # Assert
        assert response.status_code == 404
        
        # Cleanup
        app.dependency_overrides = {}
