"""ID形式バリデーション"""
import re
from typing import Optional
from .errors import ServiceErrorCode, ServiceSettingException


# ID形式パターン
TENANT_ID_PATTERN = re.compile(r'^tenant_[a-zA-Z0-9_-]{1,85}$')  # "tenant_"を除いて最大85文字
SERVICE_ID_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{0,98}[a-z0-9]$')  # 最大100文字、先頭・末尾は英数字のみ

# 長さ制限
MAX_TENANT_ID_LENGTH = 100
MAX_SERVICE_ID_LENGTH = 100
MAX_ASSIGNMENT_ID_LENGTH = 255


def validate_tenant_id(tenant_id: str, request_id: Optional[str] = None) -> None:
    """
    テナントID形式検証
    
    Args:
        tenant_id: テナントID
        request_id: リクエストID
    
    Raises:
        ServiceSettingException: フォーマットエラーまたは長さ制限超過
    
    Validation Rules:
        - 形式: "tenant_" + 英数字・ハイフン・アンダースコア
        - 最大長: 100文字
        - 先頭は必ず "tenant_"
    """
    if not tenant_id:
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT,
            request_id=request_id
        )
    
    if len(tenant_id) > MAX_TENANT_ID_LENGTH:
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_002_ID_TOO_LONG,
            request_id=request_id
        )
    
    if not TENANT_ID_PATTERN.match(tenant_id):
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT,
            request_id=request_id
        )


def validate_service_id(service_id: str, request_id: Optional[str] = None) -> None:
    """
    サービスID形式検証
    
    Args:
        service_id: サービスID
        request_id: リクエストID
    
    Raises:
        ServiceSettingException: フォーマットエラーまたは長さ制限超過
    
    Validation Rules:
        - 形式: 小文字英数字・ハイフン・アンダースコア
        - 最大長: 100文字
        - 先頭と末尾は英数字のみ（ハイフン・アンダースコア不可）
    """
    if not service_id:
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT,
            request_id=request_id
        )
    
    if len(service_id) > MAX_SERVICE_ID_LENGTH:
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_002_ID_TOO_LONG,
            request_id=request_id
        )
    
    if not SERVICE_ID_PATTERN.match(service_id):
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_004_INVALID_ID_FORMAT,
            request_id=request_id
        )


def validate_assignment_id_length(
    tenant_id: str,
    service_id: str,
    request_id: Optional[str] = None
) -> None:
    """
    ServiceAssignment ID長制限検証
    
    Args:
        tenant_id: テナントID
        service_id: サービスID
        request_id: リクエストID
    
    Raises:
        ServiceSettingException: ID長制限超過
    
    Validation Rules:
        - 形式: "assignment_{tenant_id}_{service_id}"
        - 最大長: 255文字
    """
    assignment_id = f"assignment_{tenant_id}_{service_id}"
    
    if len(assignment_id) > MAX_ASSIGNMENT_ID_LENGTH:
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_002_ID_TOO_LONG,
            request_id=request_id
        )


def validate_https_url(url: str, is_production: bool) -> None:
    """
    HTTPS URL検証（本番環境のみ）
    
    Args:
        url: 検証するURL
        is_production: 本番環境フラグ
    
    Raises:
        ValueError: 本番環境でHTTPSでない場合
    
    Note:
        開発環境ではHTTPも許可
    """
    if is_production and not url.startswith("https://"):
        raise ValueError(f"HTTPS is required in production environment: {url}")
