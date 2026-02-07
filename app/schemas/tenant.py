"""テナント関連スキーマ"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TenantCreate(BaseModel):
    """テナント作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=100)
    domains: List[str] = []


class TenantUpdate(BaseModel):
    """テナント更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domains: Optional[List[str]] = None


class TenantResponse(BaseModel):
    """テナントレスポンス"""
    id: str
    name: str
    domains: List[str]
    is_privileged: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_count: int = 0


class TenantListResponse(BaseModel):
    """テナント一覧レスポンス"""
    tenants: List[TenantResponse]
    total: int


class TenantUserAddRequest(BaseModel):
    """テナントユーザー追加リクエスト"""
    user_id: str = Field(..., description="ユーザーID")


class TenantUserResponse(BaseModel):
    """テナントユーザーレスポンス"""
    id: str
    tenant_id: str
    user_id: str
    added_at: datetime
    added_by: str
