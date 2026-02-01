"""サービス割り当てリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from common.database.repository import BaseRepository
from app.models.service_assignment import ServiceAssignment
import logging

logger = logging.getLogger(__name__)


class ServiceAssignmentRepository(BaseRepository[ServiceAssignment]):
    """サービス割り当てデータアクセス層"""

    def __init__(self, container):
        """
        ServiceAssignmentRepositoryを初期化
        
        Args:
            container: Cosmos DBコンテナクライアント
        
        Note:
            ServiceAssignmentは tenant_id をパーティションキーとして格納される
        """
        super().__init__(container, ServiceAssignment)

    async def get_assignment(
        self, 
        assignment_id: str, 
        tenant_id: str
    ) -> Optional[ServiceAssignment]:
        """
        サービス割り当て取得
        
        Args:
            assignment_id: 割り当てID（assignment_{tenant_id}_{service_id}）
            tenant_id: テナントID
        
        Returns:
            Optional[ServiceAssignment]: 割り当てが存在する場合はインスタンス、存在しない場合はNone
        """
        return await self.get(assignment_id, tenant_id)

    async def create_assignment(
        self, 
        assignment: ServiceAssignment
    ) -> ServiceAssignment:
        """
        サービス割り当て作成
        
        Args:
            assignment: 作成する割り当て
        
        Returns:
            ServiceAssignment: 作成された割り当て
        
        Raises:
            CosmosHttpResponseError: 割り当てIDが重複している場合（409 Conflict）
        """
        return await self.create(assignment)

    async def update_assignment(
        self, 
        assignment_id: str, 
        tenant_id: str, 
        data: dict
    ) -> ServiceAssignment:
        """
        サービス割り当て更新
        
        Args:
            assignment_id: 割り当てID
            tenant_id: テナントID
            data: 更新データ
        
        Returns:
            ServiceAssignment: 更新された割り当て
        
        Raises:
            ValueError: 割り当てが存在しない場合
        """
        return await self.update(assignment_id, tenant_id, data)

    async def delete_assignment(
        self, 
        assignment_id: str, 
        tenant_id: str
    ) -> None:
        """
        サービス割り当て削除
        
        Args:
            assignment_id: 割り当てID
            tenant_id: テナントID
        """
        await self.delete(assignment_id, tenant_id)

    async def list_by_tenant(
        self, 
        tenant_id: str, 
        status: Optional[str] = None
    ) -> List[ServiceAssignment]:
        """
        テナントの利用サービス一覧取得
        
        Args:
            tenant_id: テナントID
            status: ステータスフィルタ（active/suspended）
        
        Returns:
            List[ServiceAssignment]: サービス割り当て一覧
        
        Performance:
            単一パーティションクエリで高速（< 100ms）
        """
        try:
            if status:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id = @tenant_id
                      AND c.type = 'service_assignment'
                      AND c.status = @status
                    ORDER BY c.assigned_at DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id},
                    {"name": "@status", "value": status}
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id = @tenant_id
                      AND c.type = 'service_assignment'
                    ORDER BY c.assigned_at DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id}
                ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id
            )

            assignments = []
            async for item in items:
                assignments.append(ServiceAssignment(**item))

            return assignments
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list assignments by tenant: {e}")
            raise

    async def find_by_tenant_and_service(
        self, 
        tenant_id: str, 
        service_id: str
    ) -> Optional[ServiceAssignment]:
        """
        テナントとサービスIDでサービス割り当て検索（重複チェック用）
        
        Args:
            tenant_id: テナントID
            service_id: サービスID
        
        Returns:
            Optional[ServiceAssignment]: 該当する割り当て、存在しない場合はNone
        
        Note:
            決定的ID（assignment_{tenant_id}_{service_id}）を使用して高速に取得
        """
        assignment_id = f"assignment_{tenant_id}_{service_id}"
        return await self.get_assignment(assignment_id, tenant_id)

    async def list_by_service(
        self, 
        service_id: str, 
        status: Optional[str] = None
    ) -> List[ServiceAssignment]:
        """
        特定サービスを利用しているテナント一覧取得（管理用）
        
        Args:
            service_id: サービスID
            status: ステータスフィルタ（active/suspended）
        
        Returns:
            List[ServiceAssignment]: サービス割り当て一覧
        
        Warning:
            クロスパーティションクエリのため、大量データでは低速（> 500ms）
            管理機能でのみ使用を推奨
        """
        try:
            if status:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id != '_system'
                      AND c.type = 'service_assignment'
                      AND c.service_id = @service_id
                      AND c.status = @status
                    ORDER BY c.assigned_at DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": "_system"},  # テナント分離のため形式的に追加
                    {"name": "@service_id", "value": service_id},
                    {"name": "@status", "value": status}
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id != '_system'
                      AND c.type = 'service_assignment'
                      AND c.service_id = @service_id
                    ORDER BY c.assigned_at DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": "_system"},  # テナント分離のため形式的に追加
                    {"name": "@service_id", "value": service_id}
                ]

            # クロスパーティションクエリを明示的に許可
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )

            assignments = []
            async for item in items:
                assignments.append(ServiceAssignment(**item))

            return assignments
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list assignments by service: {e}")
            raise

    async def count_by_tenant(self, tenant_id: str) -> int:
        """
        テナントの利用サービス数を取得
        
        Args:
            tenant_id: テナントID
        
        Returns:
            int: 利用サービス数
        """
        try:
            query = """
                SELECT VALUE COUNT(1) 
                FROM c 
                WHERE c.tenant_id = @tenant_id
                  AND c.type = 'service_assignment'
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id
            )

            async for count in items:
                return count

            return 0
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to count assignments: {e}")
            raise

    async def count_by_service(self, service_id: str) -> int:
        """
        特定サービスを利用しているテナント数を取得（管理用）
        
        Args:
            service_id: サービスID
        
        Returns:
            int: 利用テナント数
        
        Warning:
            クロスパーティションクエリのため、大量データでは低速
        """
        try:
            query = """
                SELECT VALUE COUNT(1) 
                FROM c 
                WHERE c.tenant_id != '_system'
                  AND c.type = 'service_assignment'
                  AND c.service_id = @service_id
                  AND c.status = 'active'
            """
            parameters = [
                {"name": "@tenant_id", "value": "_system"},  # テナント分離のため形式的に追加
                {"name": "@service_id", "value": service_id}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )

            async for count in items:
                return count

            return 0
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to count assignments by service: {e}")
            raise
