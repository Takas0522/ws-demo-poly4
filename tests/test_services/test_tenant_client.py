"""TenantClient テスト"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from app.services.tenant_client import TenantClient


class Test正常系:
    """正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_return_true_when_tenant_exists(self):
        """テナントが存在する場合Trueを返す"""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act
            result = await client.verify_tenant_exists("tenant_acme", "test_token")
            
            # Assert
            assert result is True
    
    @pytest.mark.asyncio
    async def test_should_return_false_when_tenant_not_found(self):
        """テナントが存在しない場合Falseを返す"""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act
            result = await client.verify_tenant_exists("tenant_nonexistent", "test_token")
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_should_return_none_when_tenant_not_found_on_get(self):
        """テナントが存在しない場合Noneを返す(get_tenant)"""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act
            result = await client.get_tenant("tenant_nonexistent", "test_token")
            
            # Assert
            assert result is None


class Test異常系:
    """異常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_raise_timeout_exception_on_verify(self):
        """タイムアウト時にTimeoutExceptionを発生させる(verify)"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.TimeoutException):
                await client.verify_tenant_exists("tenant_acme", "test_token")
    
    @pytest.mark.asyncio
    async def test_should_raise_http_status_error_on_verify(self):
        """サービスエラー時にHTTPStatusErrorを発生させる(verify)"""
        # Arrange
        mock_request = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.request = mock_request
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await client.verify_tenant_exists("tenant_acme", "test_token")
    
    @pytest.mark.asyncio
    async def test_should_raise_timeout_exception_on_get(self):
        """タイムアウト時にTimeoutExceptionを発生させる(get)"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.TimeoutException):
                await client.get_tenant("tenant_acme", "test_token")
    
    @pytest.mark.asyncio
    async def test_should_raise_http_status_error_on_get(self):
        """サービスエラー時にHTTPStatusErrorを発生させる(get)"""
        # Arrange
        mock_request = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.request = mock_request
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_tenant("tenant_acme", "test_token")
    
    @pytest.mark.asyncio
    async def test_should_raise_request_error_on_verify(self):
        """リクエストエラー時にRequestErrorを発生させる(verify)"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.RequestError):
                await client.verify_tenant_exists("tenant_acme", "test_token")
    
    @pytest.mark.asyncio
    async def test_should_raise_request_error_on_get(self):
        """リクエストエラー時にRequestErrorを発生させる(get)"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value = mock_client
            
            client = TenantClient()
            
            # Act & Assert
            with pytest.raises(httpx.RequestError):
                await client.get_tenant("tenant_acme", "test_token")
