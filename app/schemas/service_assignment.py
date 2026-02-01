"""ServiceAssignment 関連スキーマ"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ServiceAssignmentCreate(BaseModel):
    """サービス割り当て作成リクエスト"""
    
    service_id: str = Field(
        ...,
        description="サービスID（最大100文字）",
        pattern="^[a-z0-9-]+$",
        max_length=100
    )
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="サービス固有設定（オプショナル、最大10KB）"
    )
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """config検証"""
        if v is None:
            return v
        
        # サイズ検証（最大10KB）
        json_str = json.dumps(v)
        if len(json_str.encode('utf-8')) > 10240:
            raise ValueError('config must be less than 10KB')
        
        # ネストレベル検証（最大5階層）
        def check_depth(obj: Any, current_depth: int = 1, max_depth: int = 5) -> None:
            if current_depth > max_depth:
                raise ValueError(f'config nesting level must be {max_depth} or less')
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, current_depth + 1, max_depth)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1, max_depth)
        
        check_depth(v)
        
        # 制御文字・特殊文字検証
        control_char_pattern = re.compile(r'[\x00-\x1F\x7F]')
        
        def check_control_chars(obj: Any) -> None:
            if isinstance(obj, str):
                if control_char_pattern.search(obj):
                    raise ValueError('config values must not contain control characters')
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    if not isinstance(key, str):
                        raise ValueError('config keys must be strings')
                    check_control_chars(value)
            elif isinstance(obj, list):
                for item in obj:
                    check_control_chars(item)
            elif not isinstance(obj, (str, int, float, bool, type(None))):
                raise ValueError('config values must be primitive types, objects, or arrays')
        
        check_control_chars(v)
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "messaging-service",
                "config": {
                    "max_channels": 50,
                    "max_members_per_channel": 100
                }
            }
        }


class ServiceAssignmentResponse(BaseModel):
    """サービス割り当て詳細レスポンス"""
    
    assignment_id: str = Field(..., description="割り当てID")
    tenant_id: str = Field(..., description="テナントID")
    service_id: str = Field(..., description="サービスID")
    service_name: Optional[str] = Field(None, description="サービス名")
    status: str = Field(..., description="ステータス（active/suspended）")
    config: Optional[Dict[str, Any]] = Field(None, description="サービス固有設定")
    assigned_at: datetime = Field(..., description="割り当て日時")
    assigned_by: str = Field(..., description="割り当て実行者ユーザーID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "assignment_tenant_acme_messaging-service",
                "tenant_id": "tenant_acme",
                "service_id": "messaging-service",
                "service_name": "メッセージングサービス",
                "status": "active",
                "config": {
                    "max_channels": 50,
                    "max_members_per_channel": 100
                },
                "assigned_at": "2026-02-01T10:00:00Z",
                "assigned_by": "user_admin_001"
            }
        }


class TenantServiceListResponse(BaseModel):
    """テナント利用サービス一覧レスポンス"""
    
    data: List[ServiceAssignmentResponse] = Field(..., description="サービス割り当て一覧")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "assignment_id": "assignment_tenant_acme_file-service",
                        "service_id": "file-service",
                        "service_name": "ファイル管理サービス",
                        "status": "active",
                        "config": {
                            "max_storage": "100GB",
                            "max_file_size": "10MB"
                        },
                        "assigned_at": "2026-01-10T09:00:00Z",
                        "assigned_by": "user_admin_001"
                    }
                ]
            }
        }
