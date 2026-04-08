"""サービス機能関連スキーマ"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ServiceFeatureResponse(BaseModel):
    """サービス機能マスター APIレスポンス"""
    id: str
    service_id: str
    feature_key: str
    feature_name: str
    description: str
    default_enabled: bool
    created_at: datetime


class TenantServiceFeatureResponse(BaseModel):
    """テナント別機能設定 APIレスポンス（マスターとマージ済み）"""
    feature_id: str
    service_id: str
    feature_key: str
    feature_name: str
    description: str
    is_enabled: bool              # テナント設定またはdefault_enabledの値
    is_default: bool              # TenantServiceFeatureが未設定でデフォルト値を返している場合 True
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class UpdateTenantServiceFeatureRequest(BaseModel):
    """機能の有効/無効切り替えリクエスト"""
    is_enabled: bool
