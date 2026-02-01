"""サービスカタログAPI"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
import logging

from app.schemas.service import ServiceListResponse, ServiceResponse
from app.services.service_service import ServiceService
from app.repositories.service_repository import ServiceRepository
from app.dependencies import get_cosmos_container, get_request_id
from app.utils.errors import ServiceErrorCode, ServiceSettingException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/services",
    tags=["services"]
)


def get_service_service(
    cosmos_container=Depends(get_cosmos_container)
) -> ServiceService:
    """ServiceServiceを取得"""
    service_repository = ServiceRepository(cosmos_container)
    return ServiceService(service_repository)


@router.get("", response_model=ServiceListResponse)
async def list_services(
    is_active: bool = True,
    service_service: ServiceService = Depends(get_service_service),
    request_id: str = Depends(get_request_id)
):
    """
    サービス一覧取得
    
    Args:
        is_active: アクティブ状態フィルタ（Trueの場合はアクティブなサービスのみ）
        service_service: ServiceServiceインスタンス
        request_id: リクエストID
    
    Returns:
        ServiceListResponse: サービス一覧
    
    Raises:
        ServiceSettingException: 
            - AUTH_001_INVALID_TOKEN: JWT無効または期限切れ
            - AUTH_002_INSUFFICIENT_ROLE: 必要なロールがない
            - INTERNAL_001_UNEXPECTED: 予期しないエラー
    
    Note:
        - 認証: Required（全エンドポイントでJWT認証必須）
        - 認可: service-setting: 閲覧者以上
        - パフォーマンス: < 200ms (P95)
    """
    try:
        logger.info(
            f"Fetching services list",
            extra={"is_active": is_active, "request_id": request_id}
        )
        
        # サービス一覧取得
        services = await service_service.list_services(is_active=is_active)
        
        # レスポンス作成
        service_responses = [
            ServiceResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                version=s.version,
                base_url=s.base_url,
                role_endpoint=s.role_endpoint,
                health_endpoint=s.health_endpoint,
                is_active=s.is_active,
                metadata=s.metadata,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in services
        ]
        
        logger.info(
            f"Services list retrieved successfully",
            extra={
                "service_count": len(service_responses),
                "request_id": request_id
            }
        )
        
        return ServiceListResponse(data=service_responses)
        
    except ServiceSettingException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error fetching services list",
            exc_info=True,
            extra={"error": str(e), "request_id": request_id}
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.INTERNAL_001_UNEXPECTED,
            request_id=request_id
        )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    service_service: ServiceService = Depends(get_service_service),
    request_id: str = Depends(get_request_id)
):
    """
    サービス詳細取得
    
    Args:
        service_id: サービスID
        service_service: ServiceServiceインスタンス
        request_id: リクエストID
    
    Returns:
        ServiceResponse: サービス詳細
    
    Raises:
        ServiceSettingException: 
            - AUTH_001_INVALID_TOKEN: JWT無効または期限切れ
            - AUTH_002_INSUFFICIENT_ROLE: 必要なロールがない
            - SERVICE_001_NOT_FOUND: サービスが存在しない
            - INTERNAL_001_UNEXPECTED: 予期しないエラー
    
    Note:
        - 認証: Required
        - 認可: service-setting: 閲覧者以上
        - パフォーマンス: < 100ms (P95)
    """
    try:
        logger.info(
            f"Fetching service detail",
            extra={"service_id": service_id, "request_id": request_id}
        )
        
        # サービス取得
        service = await service_service.get_service(service_id)
        
        if not service:
            logger.warning(
                f"Service not found",
                extra={"service_id": service_id, "request_id": request_id}
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.SERVICE_001_NOT_FOUND,
                request_id=request_id
            )
        
        # レスポンス作成
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
        
        logger.info(
            f"Service detail retrieved successfully",
            extra={"service_id": service_id, "request_id": request_id}
        )
        
        return response
        
    except ServiceSettingException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error fetching service detail",
            exc_info=True,
            extra={
                "service_id": service_id,
                "error": str(e),
                "request_id": request_id
            }
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.INTERNAL_001_UNEXPECTED,
            request_id=request_id
        )
