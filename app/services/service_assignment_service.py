"""サービス割り当て管理サービス"""
import asyncio
from typing import List, Optional
from datetime import datetime
import logging

from app.models.service_assignment import ServiceAssignment
from app.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.repositories.service_repository import ServiceRepository
from app.services.tenant_client import TenantClient
from app.models.service import Service
from app.utils.errors import ServiceErrorCode, ServiceSettingException
from app.utils.validators import (
    validate_tenant_id,
    validate_service_id,
    validate_assignment_id_length
)

logger = logging.getLogger(__name__)


class ServiceAssignmentService:
    """サービス割り当て管理サービス"""

    def __init__(
        self,
        assignment_repository: ServiceAssignmentRepository,
        service_repository: ServiceRepository,
        tenant_client: TenantClient
    ):
        """
        ServiceAssignmentServiceを初期化
        
        Args:
            assignment_repository: サービス割り当てリポジトリ
            service_repository: サービスリポジトリ
            tenant_client: テナント管理サービスクライアント
        """
        self.assignment_repository = assignment_repository
        self.service_repository = service_repository
        self.tenant_client = tenant_client
        self.logger = logger

    async def assign_service(
        self,
        tenant_id: str,
        service_id: str,
        config: Optional[dict],
        assigned_by: str,
        jwt_token: str,
        request_id: Optional[str] = None
    ) -> ServiceAssignment:
        """
        サービス割り当て
        
        Args:
            tenant_id: テナントID
            service_id: サービスID
            config: サービス固有設定（オプショナル）
            assigned_by: 割り当て実行者ユーザーID
            jwt_token: JWT認証トークン（テナント存在確認用）
            request_id: リクエストID
        
        Returns:
            ServiceAssignment: 作成されたサービス割り当て
        
        Raises:
            ServiceSettingException: 各種バリデーションエラー、業務エラー
        """
        # 1. ID形式検証
        validate_tenant_id(tenant_id, request_id)
        validate_service_id(service_id, request_id)
        validate_assignment_id_length(tenant_id, service_id, request_id)
        
        # 2. テナント存在確認（テナント管理サービスAPI）
        try:
            tenant_exists = await self.tenant_client.verify_tenant_exists(
                tenant_id, jwt_token
            )
            if not tenant_exists:
                self.logger.warning(
                    f"Tenant not found: {tenant_id}",
                    extra={"tenant_id": tenant_id, "request_id": request_id}
                )
                raise ServiceSettingException(
                    error_code=ServiceErrorCode.TENANT_002_NOT_FOUND,
                    request_id=request_id
                )
        except asyncio.TimeoutError:
            self.logger.error(
                f"Timeout verifying tenant: {tenant_id}",
                extra={"tenant_id": tenant_id, "request_id": request_id}
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.TENANT_SERVICE_TIMEOUT,
                request_id=request_id
            )
        except ServiceSettingException:
            raise
        except Exception as e:
            self.logger.error(
                f"Error verifying tenant: {tenant_id}, error: {e}",
                extra={"tenant_id": tenant_id, "error": str(e), "request_id": request_id}
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.TENANT_SERVICE_UNAVAILABLE,
                request_id=request_id
            )
        
        # 3. サービス存在確認
        service = await self.service_repository.get_service(service_id)
        if not service:
            self.logger.warning(
                f"Service not found: {service_id}",
                extra={"service_id": service_id, "request_id": request_id}
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.SERVICE_001_NOT_FOUND,
                request_id=request_id
            )
        
        # 4. サービスアクティブ確認
        if not service.is_active:
            self.logger.warning(
                f"Cannot assign inactive service: {service_id}",
                extra={"service_id": service_id, "request_id": request_id}
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.SERVICE_002_INACTIVE,
                request_id=request_id
            )
        
        # 5. 重複チェック（決定的ID）
        existing = await self.assignment_repository.find_by_tenant_and_service(
            tenant_id, service_id
        )
        if existing:
            self.logger.warning(
                f"Service already assigned: {service_id} to {tenant_id}",
                extra={
                    "tenant_id": tenant_id,
                    "service_id": service_id,
                    "request_id": request_id
                }
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.ASSIGNMENT_002_DUPLICATE,
                request_id=request_id
            )
        
        # 6. ServiceAssignment作成
        assignment_id = f"assignment_{tenant_id}_{service_id}"
        assignment = ServiceAssignment(
            id=assignment_id,
            tenant_id=tenant_id,
            service_id=service_id,
            status="active",
            config=config or {},
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by
        )
        
        created_assignment = await self.assignment_repository.create_assignment(
            assignment
        )
        
        # 7. 監査ログ記録（詳細情報はログに記録）
        self.logger.info(
            f"Service assigned: {service_id} to {tenant_id} by {assigned_by}",
            extra={
                "action": "service.assign",
                "target_type": "service_assignment",
                "target_id": assignment_id,
                "performed_by": assigned_by,
                "tenant_id": tenant_id,
                "service_id": service_id,
                "request_id": request_id
            }
        )
        
        return created_assignment

    async def remove_service_assignment(
        self,
        tenant_id: str,
        service_id: str,
        deleted_by: str,
        request_id: Optional[str] = None
    ) -> None:
        """
        サービス割り当て解除
        
        Args:
            tenant_id: テナントID
            service_id: サービスID
            deleted_by: 削除者ユーザーID
            request_id: リクエストID
        
        Raises:
            ServiceSettingException: ServiceAssignmentが存在しない
        
        Note:
            Phase 1では物理削除、Phase 2で論理削除に変更予定
        """
        # 1. ID形式検証
        validate_tenant_id(tenant_id, request_id)
        validate_service_id(service_id, request_id)
        
        # 2. ServiceAssignment取得
        assignment_id = f"assignment_{tenant_id}_{service_id}"
        assignment = await self.assignment_repository.get_assignment(
            assignment_id, tenant_id
        )
        
        if not assignment:
            self.logger.warning(
                f"Service assignment not found: {tenant_id}/{service_id}",
                extra={
                    "tenant_id": tenant_id,
                    "service_id": service_id,
                    "request_id": request_id
                }
            )
            raise ServiceSettingException(
                error_code=ServiceErrorCode.ASSIGNMENT_001_NOT_FOUND,
                request_id=request_id
            )
        
        # 3. 物理削除（Phase 1）
        await self.assignment_repository.delete_assignment(assignment_id, tenant_id)
        
        # 4. 監査ログ記録（詳細情報はログに記録）
        self.logger.info(
            f"Service unassigned: {service_id} from {tenant_id} by {deleted_by}",
            extra={
                "action": "service.unassign",
                "target_type": "service_assignment",
                "target_id": assignment_id,
                "performed_by": deleted_by,
                "tenant_id": tenant_id,
                "service_id": service_id,
                "request_id": request_id
            }
        )

    async def list_tenant_services(
        self,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[tuple[ServiceAssignment, Optional[Service]]]:
        """
        テナント利用サービス一覧取得
        
        Args:
            tenant_id: テナントID
            status: ステータスフィルタ（active/suspended）
        
        Returns:
            List[tuple[ServiceAssignment, Optional[Service]]]: 
                サービス割り当てとサービス情報のタプルリスト
        
        Note:
            並列Service情報取得を実装し、一部取得失敗時も他のServiceを返却
        """
        # 1. ServiceAssignment一覧取得
        assignments = await self.assignment_repository.list_by_tenant(
            tenant_id, status
        )
        
        if not assignments:
            return []
        
        # 2. 各ServiceAssignmentに対応するService情報を並列取得
        async def get_service_safe(service_id: str) -> Optional[Service]:
            """Service取得（エラーハンドリング付き）"""
            try:
                # 200msのタイムアウトを設定
                service = await asyncio.wait_for(
                    self.service_repository.get_service(service_id),
                    timeout=0.2
                )
                return service
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Timeout fetching service {service_id}",
                    extra={"service_id": service_id}
                )
                return None
            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch service {service_id}: {e}",
                    extra={"service_id": service_id, "error": str(e)}
                )
                return None
        
        # 並列Service取得
        services = await asyncio.gather(
            *[get_service_safe(a.service_id) for a in assignments],
            return_exceptions=False
        )
        
        # ServiceAssignmentとServiceをペアにして返却
        results = list(zip(assignments, services))
        
        self.logger.info(
            f"Tenant services listed: {len(assignments)} assignments, "
            f"{sum(1 for _, s in results if s is not None)} services retrieved",
            extra={
                "tenant_id": tenant_id,
                "assignment_count": len(assignments),
                "service_count": sum(1 for _, s in results if s is not None)
            }
        )
        
        return results

    async def get_service_assignment(
        self,
        tenant_id: str,
        service_id: str
    ) -> Optional[ServiceAssignment]:
        """
        サービス割り当て詳細取得
        
        Args:
            tenant_id: テナントID
            service_id: サービスID
        
        Returns:
            Optional[ServiceAssignment]: サービス割り当て、存在しない場合はNone
        """
        assignment = await self.assignment_repository.find_by_tenant_and_service(
            tenant_id, service_id
        )
        
        if assignment:
            self.logger.info(
                f"Service assignment retrieved: {tenant_id}/{service_id}"
            )
        else:
            self.logger.warning(
                f"Service assignment not found: {tenant_id}/{service_id}"
            )
        
        return assignment

    async def update_service_assignment(
        self,
        tenant_id: str,
        service_id: str,
        update_data: dict,
        updated_by: str,
        request_id: Optional[str] = None
    ) -> ServiceAssignment:
        """
        サービス割り当て更新（ステータス変更等）
        
        Args:
            tenant_id: テナントID
            service_id: サービスID
            update_data: 更新データ
            updated_by: 更新者ユーザーID
            request_id: リクエストID
        
        Returns:
            ServiceAssignment: 更新されたサービス割り当て
        
        Raises:
            ServiceSettingException: ServiceAssignmentが存在しない
        
        Note:
            Phase 1ではAPIで提供せず、Phase 2以降で実装予定
        """
        # ServiceAssignment取得
        assignment_id = f"assignment_{tenant_id}_{service_id}"
        assignment = await self.assignment_repository.get_assignment(
            assignment_id, tenant_id
        )
        
        if not assignment:
            raise ServiceSettingException(
                error_code=ServiceErrorCode.ASSIGNMENT_001_NOT_FOUND,
                request_id=request_id
            )
        
        # 更新実行
        updated_assignment = await self.assignment_repository.update_assignment(
            assignment_id, tenant_id, update_data
        )
        
        self.logger.info(
            f"Service assignment updated: {tenant_id}/{service_id} by {updated_by}",
            extra={
                "tenant_id": tenant_id,
                "service_id": service_id,
                "updated_by": updated_by,
                "request_id": request_id
            }
        )
        
        return updated_assignment

    async def count_tenant_services(self, tenant_id: str) -> int:
        """
        テナントの利用サービス数を取得
        
        Args:
            tenant_id: テナントID
        
        Returns:
            int: 利用サービス数
        """
        count = await self.assignment_repository.count_by_tenant(tenant_id)
        return count

    async def count_service_usage(self, service_id: str) -> int:
        """
        特定サービスを利用しているテナント数を取得（管理用）
        
        Args:
            service_id: サービスID
        
        Returns:
            int: 利用テナント数
        
        Warning:
            クロスパーティションクエリのため、大量データでは低速
        """
        count = await self.assignment_repository.count_by_service(service_id)
        return count
