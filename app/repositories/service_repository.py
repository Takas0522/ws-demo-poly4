"""サービスリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from common.database.repository import BaseRepository
from app.models.service import Service
import logging

logger = logging.getLogger(__name__)


class ServiceRepository(BaseRepository[Service]):
    """サービスカタログデータアクセス層"""

    def __init__(self, container):
        """
        ServiceRepositoryを初期化
        
        Args:
            container: Cosmos DBコンテナクライアント
        
        Note:
            全Serviceエンティティは tenant_id='_system' のパーティションに格納される
        """
        super().__init__(container, Service)
        self.system_partition_key = "_system"

    async def get_service(self, service_id: str) -> Optional[Service]:
        """
        サービス取得（_systemパーティション）
        
        Args:
            service_id: サービスID
        
        Returns:
            Optional[Service]: サービスが存在する場合はServiceインスタンス、存在しない場合はNone
        """
        return await self.get(service_id, self.system_partition_key)

    async def create_service(self, service: Service) -> Service:
        """
        サービス作成
        
        Args:
            service: 作成するサービス
        
        Returns:
            Service: 作成されたサービス
        
        Raises:
            CosmosHttpResponseError: サービスIDが重複している場合（409 Conflict）
        """
        return await self.create(service)

    async def update_service(self, service_id: str, data: dict) -> Service:
        """
        サービス更新
        
        Args:
            service_id: サービスID
            data: 更新データ
        
        Returns:
            Service: 更新されたサービス
        
        Raises:
            ValueError: サービスが存在しない場合
        """
        return await self.update(service_id, self.system_partition_key, data)

    async def delete_service(self, service_id: str) -> None:
        """
        サービス削除
        
        Args:
            service_id: サービスID
        """
        await self.delete(service_id, self.system_partition_key)

    async def list_all(self, is_active: Optional[bool] = True) -> List[Service]:
        """
        全サービス一覧取得
        
        Args:
            is_active: アクティブ状態フィルタ（Noneの場合はフィルタなし）
        
        Returns:
            List[Service]: サービス一覧
        
        Note:
            全サービスは _system パーティションに格納されているため、
            単一パーティションクエリで高速に取得可能（< 100ms）
        """
        try:
            if is_active is not None:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id = @tenant_id
                      AND c.type = 'service' 
                      AND c.is_active = @is_active
                    ORDER BY c.name ASC
                """
                parameters = [
                    {"name": "@tenant_id", "value": self.system_partition_key},
                    {"name": "@is_active", "value": is_active}
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenant_id = @tenant_id
                      AND c.type = 'service'
                    ORDER BY c.name ASC
                """
                parameters = [
                    {"name": "@tenant_id", "value": self.system_partition_key}
                ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=self.system_partition_key
            )

            services = []
            async for item in items:
                services.append(Service(**item))

            return services
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list services: {e}")
            raise

    async def find_by_name(self, name: str) -> Optional[Service]:
        """
        サービス名でサービス検索
        
        Args:
            name: サービス名
        
        Returns:
            Optional[Service]: 該当するサービス、存在しない場合はNone
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenant_id = @tenant_id
                  AND c.type = 'service' 
                  AND c.name = @name
            """
            parameters = [
                {"name": "@tenant_id", "value": self.system_partition_key},
                {"name": "@name", "value": name}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=self.system_partition_key
            )

            async for item in items:
                return Service(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find service by name: {e}")
            raise

    async def count_active_services(self) -> int:
        """
        アクティブなサービスの数を取得
        
        Returns:
            int: アクティブなサービス数
        """
        try:
            query = """
                SELECT VALUE COUNT(1) 
                FROM c 
                WHERE c.tenant_id = @tenant_id
                  AND c.type = 'service' 
                  AND c.is_active = true
            """
            parameters = [
                {"name": "@tenant_id", "value": self.system_partition_key}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=self.system_partition_key
            )

            async for count in items:
                return count

            return 0
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to count active services: {e}")
            raise
