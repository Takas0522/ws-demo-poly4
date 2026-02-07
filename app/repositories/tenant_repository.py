"""テナントリポジトリ"""
from azure.cosmos import CosmosClient
from typing import Optional, List
from ..models.tenant import Tenant, TenantUser
from ..config import get_settings

settings = get_settings()


class TenantRepository:
    """テナントデータアクセス"""

    def __init__(self):
        self.client = CosmosClient(
            settings.cosmos_db_endpoint,
            settings.cosmos_db_key,
            connection_verify=settings.cosmos_db_connection_verify,
            connection_mode="Gateway",  # エミュレーター用にGatewayモードを使用
            enable_endpoint_discovery=False  # IPリダイレクトを無効化
        )
        self.database = self.client.get_database_client(
            settings.cosmos_db_database)
        self.container = self.database.get_container_client(
            settings.cosmos_db_container)

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """IDでテナント取得"""
        query = "SELECT * FROM c WHERE c.type = 'tenant' AND c.id = @id"
        parameters = [{"name": "@id", "value": tenant_id}]

        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if items:
            return Tenant(**items[0])
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """全テナント取得"""
        query = "SELECT * FROM c WHERE c.type = 'tenant' OFFSET @skip LIMIT @limit"
        parameters = [
            {"name": "@skip", "value": skip},
            {"name": "@limit", "value": limit}
        ]

        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        return [Tenant(**item) for item in items]

    async def create(self, tenant: Tenant) -> Tenant:
        """テナント作成"""
        tenant_dict = tenant.model_dump(by_alias=True)
        self.container.create_item(tenant_dict)
        return tenant

    async def update(self, tenant: Tenant) -> Tenant:
        """テナント更新"""
        tenant_dict = tenant.model_dump(by_alias=True)
        self.container.upsert_item(tenant_dict)
        return tenant

    async def delete(self, tenant_id: str, partition_key: str) -> bool:
        """テナント削除"""
        try:
            self.container.delete_item(tenant_id, partition_key=partition_key)
            return True
        except Exception:
            return False

    async def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """テナントのユーザー一覧取得"""
        query = "SELECT * FROM c WHERE c.type = 'tenant_user' AND c.tenantId = @tenantId"
        parameters = [{"name": "@tenantId", "value": tenant_id}]

        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        return [TenantUser(**item) for item in items]

    async def add_user_to_tenant(self, tenant_user: TenantUser) -> TenantUser:
        """テナントにユーザー追加"""
        tenant_user_dict = tenant_user.model_dump(by_alias=True)
        self.container.create_item(tenant_user_dict)
        return tenant_user

    async def remove_user_from_tenant(self, tenant_user_id: str, partition_key: str) -> bool:
        """テナントからユーザー削除"""
        try:
            self.container.delete_item(
                tenant_user_id, partition_key=partition_key)
            return True
        except Exception:
            return False
