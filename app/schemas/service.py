"""Service 関連スキーマ"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ServiceResponse(BaseModel):
    """サービス詳細レスポンス"""
    
    id: str = Field(..., description="サービスID")
    name: str = Field(..., description="サービス名")
    description: str = Field(..., description="サービス説明")
    version: str = Field(..., description="バージョン")
    base_url: Optional[str] = Field(None, description="サービスのベースURL")
    role_endpoint: Optional[str] = Field(None, description="ロール情報取得エンドポイント")
    health_endpoint: Optional[str] = Field(None, description="ヘルスチェックエンドポイント")
    is_active: bool = Field(..., description="アクティブ状態")
    metadata: Optional[dict] = Field(None, description="追加メタデータ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "file-service",
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
                },
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z"
            }
        }


class ServiceListResponse(BaseModel):
    """サービス一覧レスポンス"""
    
    data: List[ServiceResponse] = Field(..., description="サービス一覧")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "file-service",
                        "name": "ファイル管理サービス",
                        "description": "ファイルのアップロード・ダウンロード・管理",
                        "version": "1.0.0",
                        "is_active": True,
                        "metadata": {
                            "icon": "file-icon.png",
                            "category": "storage"
                        }
                    }
                ]
            }
        }
