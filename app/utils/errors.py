"""エラーコード定義と標準化エラー処理"""
from enum import Enum
from typing import Optional, List, Any
from fastapi import HTTPException
from common.models.errors import ErrorResponse, ErrorDetail


class ServiceErrorCode(str, Enum):
    """サービス設定サービスのエラーコード"""
    
    # 認証エラー (401)
    AUTH_001_INVALID_TOKEN = "AUTH_001_INVALID_TOKEN"
    
    # 認可エラー (403)
    AUTH_002_INSUFFICIENT_ROLE = "AUTH_002_INSUFFICIENT_ROLE"
    TENANT_001_ACCESS_DENIED = "TENANT_001_ACCESS_DENIED"
    
    # Not Found (404)
    SERVICE_001_NOT_FOUND = "SERVICE_001_NOT_FOUND"
    TENANT_002_NOT_FOUND = "TENANT_002_NOT_FOUND"
    ASSIGNMENT_001_NOT_FOUND = "ASSIGNMENT_001_NOT_FOUND"
    
    # Conflict (409)
    ASSIGNMENT_002_DUPLICATE = "ASSIGNMENT_002_DUPLICATE"
    
    # Unprocessable Entity (422)
    SERVICE_002_INACTIVE = "SERVICE_002_INACTIVE"
    
    # Bad Request (400)
    VALIDATION_001_INVALID_INPUT = "VALIDATION_001_INVALID_INPUT"
    VALIDATION_002_ID_TOO_LONG = "VALIDATION_002_ID_TOO_LONG"
    VALIDATION_003_CONFIG_INVALID = "VALIDATION_003_CONFIG_INVALID"
    VALIDATION_004_INVALID_ID_FORMAT = "VALIDATION_004_INVALID_ID_FORMAT"
    
    # Service Unavailable (503)
    TENANT_SERVICE_UNAVAILABLE = "TENANT_SERVICE_UNAVAILABLE"
    DB_001_CONNECTION_ERROR = "DB_001_CONNECTION_ERROR"
    
    # Gateway Timeout (504)
    DB_002_TIMEOUT = "DB_002_TIMEOUT"
    TENANT_SERVICE_TIMEOUT = "TENANT_SERVICE_TIMEOUT"
    
    # Internal Server Error (500)
    INTERNAL_001_UNEXPECTED = "INTERNAL_001_UNEXPECTED"


# エラーコードとメッセージのマッピング（汎用メッセージのみ）
ERROR_MESSAGES = {
    # 認証エラー
    ServiceErrorCode.AUTH_001_INVALID_TOKEN: "Invalid or expired authentication token",
    ServiceErrorCode.AUTH_002_INSUFFICIENT_ROLE: "Insufficient permissions for this operation",
    ServiceErrorCode.TENANT_001_ACCESS_DENIED: "Access to the requested resource is denied",
    
    # Not Found
    ServiceErrorCode.SERVICE_001_NOT_FOUND: "The requested service does not exist",
    ServiceErrorCode.TENANT_002_NOT_FOUND: "The requested tenant does not exist",
    ServiceErrorCode.ASSIGNMENT_001_NOT_FOUND: "The requested service assignment does not exist",
    
    # Conflict
    ServiceErrorCode.ASSIGNMENT_002_DUPLICATE: "Service is already assigned to this tenant",
    
    # Unprocessable Entity
    ServiceErrorCode.SERVICE_002_INACTIVE: "Cannot assign inactive service",
    
    # Bad Request
    ServiceErrorCode.VALIDATION_001_INVALID_INPUT: "Request validation failed",
    ServiceErrorCode.VALIDATION_002_ID_TOO_LONG: "Identifier exceeds maximum length",
    ServiceErrorCode.VALIDATION_003_CONFIG_INVALID: "Invalid configuration structure",
    ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT: "Invalid identifier format",
    
    # Service Unavailable
    ServiceErrorCode.TENANT_SERVICE_UNAVAILABLE: "Tenant service is currently unavailable",
    ServiceErrorCode.DB_001_CONNECTION_ERROR: "Database connection error",
    
    # Gateway Timeout
    ServiceErrorCode.DB_002_TIMEOUT: "Database operation timeout",
    ServiceErrorCode.TENANT_SERVICE_TIMEOUT: "Tenant service timeout",
    
    # Internal Server Error
    ServiceErrorCode.INTERNAL_001_UNEXPECTED: "An unexpected error occurred",
}


# エラーコードとHTTPステータスコードのマッピング
ERROR_STATUS_CODES = {
    ServiceErrorCode.AUTH_001_INVALID_TOKEN: 401,
    ServiceErrorCode.AUTH_002_INSUFFICIENT_ROLE: 403,
    ServiceErrorCode.TENANT_001_ACCESS_DENIED: 403,
    ServiceErrorCode.SERVICE_001_NOT_FOUND: 404,
    ServiceErrorCode.TENANT_002_NOT_FOUND: 404,
    ServiceErrorCode.ASSIGNMENT_001_NOT_FOUND: 404,
    ServiceErrorCode.ASSIGNMENT_002_DUPLICATE: 409,
    ServiceErrorCode.SERVICE_002_INACTIVE: 422,
    ServiceErrorCode.VALIDATION_001_INVALID_INPUT: 400,
    ServiceErrorCode.VALIDATION_002_ID_TOO_LONG: 400,
    ServiceErrorCode.VALIDATION_003_CONFIG_INVALID: 400,
    ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT: 400,
    ServiceErrorCode.TENANT_SERVICE_UNAVAILABLE: 503,
    ServiceErrorCode.DB_001_CONNECTION_ERROR: 503,
    ServiceErrorCode.DB_002_TIMEOUT: 504,
    ServiceErrorCode.TENANT_SERVICE_TIMEOUT: 504,
    ServiceErrorCode.INTERNAL_001_UNEXPECTED: 500,
}


class ServiceSettingException(HTTPException):
    """サービス設定サービス標準化例外"""
    
    def __init__(
        self,
        error_code: ServiceErrorCode,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None
    ):
        """
        標準化例外を作成
        
        Args:
            error_code: エラーコード
            details: エラー詳細（内部情報はログのみに記録、ユーザーには返さない）
            request_id: リクエストID
        """
        status_code = ERROR_STATUS_CODES.get(error_code, 500)
        message = ERROR_MESSAGES.get(error_code, "An error occurred")
        
        # ErrorResponseを作成
        error_response = ErrorResponse(
            code=error_code.value,
            message=message,
            details=details,
            request_id=request_id
        )
        
        super().__init__(
            status_code=status_code,
            detail=error_response.model_dump(mode='json')
        )
