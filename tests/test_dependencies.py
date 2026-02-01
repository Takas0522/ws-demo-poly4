"""dependencies テスト"""
import pytest
from fastapi import Request
from unittest.mock import MagicMock, AsyncMock
from app.dependencies import (
    get_jwt_token
)


class Test正常系:
    """正常系テスト"""
    
    def test_should_get_jwt_token_from_bearer_authorization(self):
        """Bearer形式のAuthorizationからJWTトークンを取得する"""
        # Arrange
        authorization_header = "Bearer test-token-123"
        
        # Act
        token = get_jwt_token(authorization_header)
        
        # Assert
        assert token == "test-token-123"
    
    def test_should_return_none_when_no_authorization_header(self):
        """Authorizationヘッダーがない場合Noneを返す"""
        # Arrange
        authorization_header = None
        
        # Act
        token = get_jwt_token(authorization_header)
        
        # Assert
        assert token is None
    
    def test_should_return_none_when_invalid_authorization_format(self):
        """不正なAuthorization形式の場合Noneを返す"""
        # Arrange
        authorization_header = "InvalidFormat token"
        
        # Act
        token = get_jwt_token(authorization_header)
        
        # Assert
        assert token is None
