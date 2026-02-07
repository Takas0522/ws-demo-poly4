"""テナントサービス"""
from typing import List, Optional
from datetime import datetime
import uuid
from ..models.tenant import Tenant, TenantUser
from ..repositories.tenant_repository import TenantRepository
from ..schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from ..config import get_settings

settings = get_settings()


class TenantService:
    """テナントビジネスロジック"""
    
    def __init__(self):
        self.tenant_repo = TenantRepository()
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantResponse]:
        """テナント取得"""
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None
        
        # ユーザー数取得
        users = await self.tenant_repo.get_tenant_users(tenant_id)
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            domains=tenant.domains,
            is_privileged=tenant.is_privileged,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            user_count=len(users)
        )
    
    async def get_all_tenants(self, skip: int = 0, limit: int = 100) -> List[TenantResponse]:
        """テナント一覧取得"""
        tenants = await self.tenant_repo.get_all(skip=skip, limit=limit)
        
        responses = []
        for tenant in tenants:
            users = await self.tenant_repo.get_tenant_users(tenant.id)
            responses.append(
                TenantResponse(
                    id=tenant.id,
                    name=tenant.name,
                    domains=tenant.domains,
                    is_privileged=tenant.is_privileged,
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at,
                    user_count=len(users)
                )
            )
        
        return responses
    
    async def create_tenant(self, tenant_create: TenantCreate) -> TenantResponse:
        """テナント作成"""
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            type="tenant",
            name=tenant_create.name,
            domains=tenant_create.domains,
            isPrivileged=False,
            createdAt=datetime.utcnow(),
            partitionKey=tenant_id
        )
        
        created_tenant = await self.tenant_repo.create(tenant)
        
        return TenantResponse(
            id=created_tenant.id,
            name=created_tenant.name,
            domains=created_tenant.domains,
            is_privileged=created_tenant.is_privileged,
            created_at=created_tenant.created_at,
            updated_at=created_tenant.updated_at,
            user_count=0
        )
    
    async def update_tenant(
        self,
        tenant_id: str,
        tenant_update: TenantUpdate
    ) -> Optional[TenantResponse]:
        """テナント更新"""
        # 特権テナント保護
        if tenant_id == settings.privileged_tenant_id:
            raise ValueError("Cannot update privileged tenant")
        
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None
        
        # 更新
        if tenant_update.name is not None:
            tenant.name = tenant_update.name
        if tenant_update.domains is not None:
            tenant.domains = tenant_update.domains
        
        tenant.updated_at = datetime.utcnow()
        
        updated_tenant = await self.tenant_repo.update(tenant)
        
        # ユーザー数取得
        users = await self.tenant_repo.get_tenant_users(tenant_id)
        
        return TenantResponse(
            id=updated_tenant.id,
            name=updated_tenant.name,
            domains=updated_tenant.domains,
            is_privileged=updated_tenant.is_privileged,
            created_at=updated_tenant.created_at,
            updated_at=updated_tenant.updated_at,
            user_count=len(users)
        )
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """テナント削除"""
        # 特権テナント保護
        if tenant_id == settings.privileged_tenant_id:
            raise ValueError("Cannot delete privileged tenant")
        
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return False
        
        return await self.tenant_repo.delete(tenant_id, tenant.partition_key)
    
    async def add_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        added_by: str
    ) -> bool:
        """テナントにユーザー追加"""
        # テナント存在確認
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return False
        
        # テナントユーザー作成
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            type="tenant_user",
            tenantId=tenant_id,
            userId=user_id,
            addedAt=datetime.utcnow(),
            addedBy=added_by,
            partitionKey=tenant_id
        )
        
        await self.tenant_repo.add_user_to_tenant(tenant_user)
        return True
    
    async def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """テナントのユーザー一覧取得"""
        return await self.tenant_repo.get_tenant_users(tenant_id)
