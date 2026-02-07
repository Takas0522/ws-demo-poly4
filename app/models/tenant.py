"""テナントモデル"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class Tenant(BaseModel):
    """テナントモデル"""
    id: str
    type: str = "tenant"
    name: str
    domains: List[str] = []
    is_privileged: bool = Field(False, alias="isPrivileged")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    partition_key: str = Field(..., alias="partitionKey")
    
    class Config:
        populate_by_name = True


class TenantUser(BaseModel):
    """テナントユーザー紐付けモデル"""
    id: str
    type: str = "tenant_user"
    tenant_id: str = Field(..., alias="tenantId")
    user_id: str = Field(..., alias="userId")
    added_at: datetime = Field(..., alias="addedAt")
    added_by: str = Field(..., alias="addedBy")
    partition_key: str = Field(..., alias="partitionKey")
    
    class Config:
        populate_by_name = True
