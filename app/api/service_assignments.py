"""サービス割り当てAPI"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, status
import logging

from app.schemas.service_assignment import (
    ServiceAssignmentCreate,
    ServiceAssignmentResponse,
    TenantServiceListResponse
)
from app.services.service_assignment_service import ServiceAssignmentService
from app.services.service_service import ServiceService
from app.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.repositories.service_repository import ServiceRepository
from app.services.tenant_client import TenantClient
from app.dependencies import (
    get_cosmos_container,
    get_request_id,
    get_jwt_token,
    get_current_user
)
from app.utils.errors import ServiceErrorCode, ServiceSettingException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tenants",
    tags=["service_assignments"]
)


def get_service_assignment_service(
    cosmos_container=Depends(get_cosmos_container)
) -> ServiceAssignmentService:
    """ServiceAssignmentServiceを取得"""
    assignment_repository = ServiceAssignmentRepository(cosmos_container)
    service_repository = ServiceRepository(cosmos_container)
    tenant_client = TenantClient()
    return ServiceAssignmentService(
        assignment_repository,
        service_repository,
        tenant_client
    )


def get_service_service(
    cosmos_container=Depends(get_cosmos_container)
) -> ServiceService:
    """ServiceServiceを取得"""
    service_repository = ServiceRepository(cosmos_container)
    return ServiceService(service_repository)


@router.get("/{tenant_id}/services", response_model=TenantServiceListResponse)
async def list_tenant_services(
    tenant_id: str,
    status: Optional[str] = None,
    service_assignment_service: ServiceAssignmentService = Depends(get_service_assignment_service),
    service_service: ServiceService = Depends(get_service_service),
    request_id: str = Depends(get_request_id),
    current_user: dict = Depends(get_current_user)
):
    """
    テナント利用サービス一覧取得
    
    Args:
        tenant_id: テナントID
        status: ステータスフィルタ（active/suspended）
        service_assignment_service: ServiceAssignmentServiceインスタンス
        service_service: ServiceServiceインスタンス
        request_id: リクエストID
        current_user: 現在のユーザー情報
    
    Returns:
        TenantServiceListResponse: テナント利用サービス一覧
    
    Raises:
        ServiceSettingException: 
            - AUTH_001_INVALID_TOKEN: JWT無効または期限切れ
            - AUTH_002_INSUFFICIENT_ROLE: 必要なロールがない
            - TENANT_001_ACCESS_DENIED: テナント分離違反
            - TENANT_002_NOT_FOUND: テナントが存在しない
            - VALIDATION_001_INVALID_INPUT: 無効なステータスフィルタ
    
    Note:
        - 認証: Required
        - 認可: service-setting: 閲覧者以上（特権テナント以外は自テナントのみ）
        - パフォーマンス: < 300ms (P95)（並列Service情報取得を含む）
    """
    try:
        logger.info(
            f"Fetching tenant services",
            extra={
                "tenant_id": tenant_id,
                "status": status,
                "request_id": request_id,
                "user_id": current_user.get("user_id")
            }
        )
        
        # ステータスフィルタ検証
        if status and status not in ["active", "suspended"]:
            raise ServiceSettingException(
                error_code=ServiceErrorCode.VALIDATION_001_INVALID_INPUT,
                request_id=request_id
            )
        
        # TODO: テナント分離チェック（特権テナント以外は自テナントのみアクセス可能）
        # 実装は共通ライブラリのJWT認証ミドルウェア連携後に追加
        
        # テナント利用サービス一覧取得
        assignments_with_services = await service_assignment_service.list_tenant_services(
            tenant_id, status
        )
        
        # レスポンス作成
        responses = []
        for assignment, service in assignments_with_services:
            responses.append(
                ServiceAssignmentResponse(
                    assignment_id=assignment.id,
                    tenant_id=assignment.tenant_id,
                    service_id=assignment.service_id,
                    service_name=service.name if service else None,
                    status=assignment.status,
                    config=assignment.config,
                    assigned_at=assignment.assigned_at,
                    assigned_by=assignment.assigned_by
                )
            )
        
        logger.info(
            f"Tenant services retrieved successfully",
            extra={
                "tenant_id": tenant_id,
                "assignment_count": len(responses),
                "request_id": request_id
            }
        )
        
        return TenantServiceListResponse(data=responses)
        
    except ServiceSettingException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error fetching tenant services",
            exc_info=True,
            extra={
                "tenant_id": tenant_id,
                "error": str(e),
                "request_id": request_id
            }
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.INTERNAL_001_UNEXPECTED,
            request_id=request_id
        )


@router.post("/{tenant_id}/services", response_model=ServiceAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_service(
    tenant_id: str,
    assignment_create: ServiceAssignmentCreate,
    service_assignment_service: ServiceAssignmentService = Depends(get_service_assignment_service),
    service_service: ServiceService = Depends(get_service_service),
    request_id: str = Depends(get_request_id),
    jwt_token: str = Depends(get_jwt_token),
    current_user: dict = Depends(get_current_user)
):
    """
    サービス割り当て
    
    Args:
        tenant_id: テナントID
        assignment_create: サービス割り当て作成リクエスト
        service_assignment_service: ServiceAssignmentServiceインスタンス
        service_service: ServiceServiceインスタンス
        request_id: リクエストID
        jwt_token: JWTトークン
        current_user: 現在のユーザー情報
    
    Returns:
        ServiceAssignmentResponse: 作成されたサービス割り当て
    
    Raises:
        ServiceSettingException: 
            - VALIDATION_001_INVALID_INPUT: バリデーションエラー
            - VALIDATION_002_ID_TOO_LONG: ID長制限超過
            - VALIDATION_004_INVALID_ID_FORMAT: ID形式エラー
            - AUTH_001_INVALID_TOKEN: JWT無効または期限切れ
            - AUTH_002_INSUFFICIENT_ROLE: 必要なロールがない
            - SERVICE_001_NOT_FOUND: サービスが存在しない
            - TENANT_002_NOT_FOUND: テナントが存在しない
            - ASSIGNMENT_002_DUPLICATE: 同一サービスが既に割り当て済み
            - SERVICE_002_INACTIVE: サービスが非アクティブ
            - TENANT_SERVICE_UNAVAILABLE: テナント管理サービスが利用不可
            - TENANT_SERVICE_TIMEOUT: テナント管理サービスがタイムアウト
    
    Note:
        - 認証: Required
        - 認可: service-setting: 全体管理者のみ
        - パフォーマンス: < 300ms (P95)
    """
    try:
        logger.info(
            f"Assigning service",
            extra={
                "tenant_id": tenant_id,
                "service_id": assignment_create.service_id,
                "request_id": request_id,
                "user_id": current_user.get("user_id")
            }
        )
        
        # TODO: 全体管理者ロールチェック
        # 実装は共通ライブラリのロール認可ミドルウェア連携後に追加
        
        assigned_by = current_user.get("user_id", "user_admin_001")
        
        # サービス割り当て
        assignment = await service_assignment_service.assign_service(
            tenant_id=tenant_id,
            service_id=assignment_create.service_id,
            config=assignment_create.config,
            assigned_by=assigned_by,
            jwt_token=jwt_token or "dummy_token",
            request_id=request_id
        )
        
        # サービス情報を取得
        service = await service_service.get_service(assignment.service_id)
        
        # レスポンス作成
        response = ServiceAssignmentResponse(
            assignment_id=assignment.id,
            tenant_id=assignment.tenant_id,
            service_id=assignment.service_id,
            service_name=service.name if service else None,
            status=assignment.status,
            config=assignment.config,
            assigned_at=assignment.assigned_at,
            assigned_by=assignment.assigned_by
        )
        
        logger.info(
            f"Service assigned successfully",
            extra={
                "assignment_id": assignment.id,
                "tenant_id": tenant_id,
                "service_id": assignment.service_id,
                "request_id": request_id
            }
        )
        
        return response
        
    except ServiceSettingException:
        raise
    except ValueError as e:
        # Pydanticバリデーションエラー
        logger.warning(
            f"Validation error",
            extra={"error": str(e), "request_id": request_id}
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.VALIDATION_001_INVALID_INPUT,
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            f"Unexpected error assigning service",
            exc_info=True,
            extra={
                "tenant_id": tenant_id,
                "service_id": assignment_create.service_id,
                "error": str(e),
                "request_id": request_id
            }
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.INTERNAL_001_UNEXPECTED,
            request_id=request_id
        )


@router.delete("/{tenant_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_service_assignment(
    tenant_id: str,
    service_id: str,
    service_assignment_service: ServiceAssignmentService = Depends(get_service_assignment_service),
    request_id: str = Depends(get_request_id),
    current_user: dict = Depends(get_current_user)
):
    """
    サービス割り当て解除
    
    Args:
        tenant_id: テナントID
        service_id: サービスID
        service_assignment_service: ServiceAssignmentServiceインスタンス
        request_id: リクエストID
        current_user: 現在のユーザー情報
    
    Returns:
        None (204 No Content)
    
    Raises:
        ServiceSettingException: 
            - AUTH_001_INVALID_TOKEN: JWT無効または期限切れ
            - AUTH_002_INSUFFICIENT_ROLE: 必要なロールがない
            - ASSIGNMENT_001_NOT_FOUND: ServiceAssignmentが存在しない
            - VALIDATION_004_INVALID_ID_FORMAT: ID形式エラー
    
    Note:
        - 認証: Required
        - 認可: service-setting: 全体管理者のみ
        - パフォーマンス: < 200ms (P95)
        - Phase 1では物理削除、Phase 2で論理削除に変更予定
    """
    try:
        logger.info(
            f"Removing service assignment",
            extra={
                "tenant_id": tenant_id,
                "service_id": service_id,
                "request_id": request_id,
                "user_id": current_user.get("user_id")
            }
        )
        
        # TODO: 全体管理者ロールチェック
        # 実装は共通ライブラリのロール認可ミドルウェア連携後に追加
        
        deleted_by = current_user.get("user_id", "user_admin_001")
        
        # サービス割り当て解除
        await service_assignment_service.remove_service_assignment(
            tenant_id=tenant_id,
            service_id=service_id,
            deleted_by=deleted_by,
            request_id=request_id
        )
        
        logger.info(
            f"Service assignment removed successfully",
            extra={
                "tenant_id": tenant_id,
                "service_id": service_id,
                "request_id": request_id
            }
        )
        
        # 204 No Content（レスポンスボディなし）
        return None
        
    except ServiceSettingException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error removing service assignment",
            exc_info=True,
            extra={
                "tenant_id": tenant_id,
                "service_id": service_id,
                "error": str(e),
                "request_id": request_id
            }
        )
        raise ServiceSettingException(
            error_code=ServiceErrorCode.INTERNAL_001_UNEXPECTED,
            request_id=request_id
        )
