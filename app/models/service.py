"""Service エンティティモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Service(BaseModel):
    """サービスカタログのサービスエンティティ"""
    
    id: str = Field(
        ...,
        description="サービスID（例: 'file-service'）",
        pattern="^[a-z0-9-]+$",
        max_length=100
    )
    tenant_id: str = Field(
        default="_system",
        description="パーティションキー（システム共通）"
    )
    type: str = Field(
        default="service",
        description="Cosmos DB識別子"
    )
    name: str = Field(
        ...,
        description="サービス名",
        min_length=1,
        max_length=200
    )
    description: str = Field(
        ...,
        description="サービス説明",
        max_length=1000
    )
    version: str = Field(
        default="1.0.0",
        description="バージョン",
        max_length=20
    )
    base_url: Optional[str] = Field(
        None,
        description="サービスのベースURL"
    )
    role_endpoint: Optional[str] = Field(
        default="/api/v1/roles",
        description="ロール情報取得エンドポイント"
    )
    health_endpoint: Optional[str] = Field(
        default="/health",
        description="ヘルスチェックエンドポイント"
    )
    is_active: bool = Field(
        default=True,
        description="アクティブ状態"
    )
    metadata: Optional[dict] = Field(
        None,
        description="追加メタデータ（アイコン、カテゴリ等）"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="作成日時"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新日時"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "file-service",
                "tenant_id": "_system",
                "type": "service",
                "name": "ファイル管理サービス",
                "description": "ファイルのアップロード・ダウンロード・管理",
                "version": "1.0.0",
                "base_url": "https://file-service.example.com",
                "role_endpoint": "/api/v1/roles",
                "health_endpoint": "/health",
                "is_active": True,
                "metadata": {
                    "icon": "file-icon.png",
                    "category": "storage"
                }
            }
        }
