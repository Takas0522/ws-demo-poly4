"""ServiceAssignment エンティティモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ServiceAssignment(BaseModel):
    """テナントへのサービス割り当てエンティティ"""
    
    id: str = Field(
        ...,
        description="割り当てID（assignment_{tenantId}_{serviceId}）",
        max_length=255
    )
    tenant_id: str = Field(
        ...,
        description="テナントID（パーティションキー）",
        pattern="^tenant_[a-zA-Z0-9_]+$",
        max_length=100
    )
    type: str = Field(
        default="service_assignment",
        description="Cosmos DB識別子"
    )
    service_id: str = Field(
        ...,
        description="サービスID",
        pattern="^[a-z0-9-]+$",
        max_length=100
    )
    status: str = Field(
        default="active",
        description="ステータス（active/suspended）",
        pattern="^(active|suspended)$"
    )
    config: Optional[dict] = Field(
        None,
        description="サービス固有設定（オプショナル、最大10KB）"
    )
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="割り当て日時"
    )
    assigned_by: str = Field(
        ...,
        description="割り当て実行者ユーザーID",
        max_length=100
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "assignment_tenant_acme_file-service",
                "tenant_id": "tenant_acme",
                "type": "service_assignment",
                "service_id": "file-service",
                "status": "active",
                "config": {
                    "max_storage": "100GB",
                    "max_file_size": "10MB"
                },
                "assigned_by": "user_admin_001"
            }
        }
