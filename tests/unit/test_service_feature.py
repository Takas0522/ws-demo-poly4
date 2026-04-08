"""
TenantServiceFeature の未設定時デフォルト値適用ロジックのユニットテスト
"""
import pytest
from datetime import datetime
from app.models.service_feature import ServiceFeature, TenantServiceFeature
from app.utils.service_feature_merge import merge_tenant_service_features


def make_feature(
    feature_id: str,
    feature_key: str,
    default_enabled: bool,
    service_id: str = "service-004",
) -> ServiceFeature:
    return ServiceFeature(
        id=feature_id,
        service_id=service_id,
        feature_key=feature_key,
        feature_name=feature_key,
        description="",
        default_enabled=default_enabled,
        created_at=datetime(2026, 1, 1),
        partitionKey=service_id,
    )


def make_tenant_setting(
    tenant_id: str,
    feature_id: str,
    feature_key: str,
    is_enabled: bool,
    service_id: str = "service-004",
) -> TenantServiceFeature:
    return TenantServiceFeature(
        id=f"{tenant_id}_{feature_id}",
        tenant_id=tenant_id,
        service_id=service_id,
        feature_id=feature_id,
        feature_key=feature_key,
        is_enabled=is_enabled,
        updated_at=datetime(2026, 2, 1),
        updated_by="admin-user-001",
        partitionKey=tenant_id,
    )


class TestMergeTenantServiceFeatures:
    """merge_tenant_service_features のユニットテスト"""

    def test_no_tenant_settings_uses_default_enabled_true(self):
        """テナント設定未登録時に default_enabled=True の機能は有効で返る"""
        features = [make_feature("feature-001", "audit_log", default_enabled=True)]

        result = merge_tenant_service_features(features, tenant_settings=[])

        assert len(result) == 1
        assert result[0].is_enabled is True
        assert result[0].is_default is True

    def test_no_tenant_settings_uses_default_enabled_false(self):
        """テナント設定未登録時に default_enabled=False の機能は無効で返る"""
        features = [make_feature("feature-001", "file_sharing", default_enabled=False)]

        result = merge_tenant_service_features(features, tenant_settings=[])

        assert len(result) == 1
        assert result[0].is_enabled is False
        assert result[0].is_default is True

    def test_tenant_setting_overrides_default_enabled(self):
        """テナント設定が存在する場合は default_enabled に優先して is_enabled が返る"""
        features = [make_feature("feature-001", "file_sharing", default_enabled=False)]
        tenant_settings = [
            make_tenant_setting("tenant-001", "feature-001", "file_sharing", is_enabled=True)
        ]

        result = merge_tenant_service_features(features, tenant_settings)

        assert result[0].is_enabled is True
        assert result[0].is_default is False

    def test_tenant_setting_can_disable_default_enabled_feature(self):
        """テナント設定で default_enabled=True の機能を無効化できる"""
        features = [make_feature("feature-001", "audit_log", default_enabled=True)]
        tenant_settings = [
            make_tenant_setting("tenant-001", "feature-001", "audit_log", is_enabled=False)
        ]

        result = merge_tenant_service_features(features, tenant_settings)

        assert result[0].is_enabled is False
        assert result[0].is_default is False

    def test_partial_tenant_settings_mixes_default_and_custom(self):
        """一部機能のみテナント設定がある場合、未設定分はデフォルト値が適用される"""
        features = [
            make_feature("feature-001", "file_sharing", default_enabled=False),
            make_feature("feature-002", "large_file_upload", default_enabled=True),
            make_feature("feature-003", "version_control", default_enabled=False),
        ]
        tenant_settings = [
            make_tenant_setting("tenant-001", "feature-001", "file_sharing", is_enabled=True),
        ]

        result = merge_tenant_service_features(features, tenant_settings)

        assert len(result) == 3
        # テナント設定あり → カスタム値
        assert result[0].feature_key == "file_sharing"
        assert result[0].is_enabled is True
        assert result[0].is_default is False
        # テナント設定なし → デフォルト値 (True)
        assert result[1].feature_key == "large_file_upload"
        assert result[1].is_enabled is True
        assert result[1].is_default is True
        # テナント設定なし → デフォルト値 (False)
        assert result[2].feature_key == "version_control"
        assert result[2].is_enabled is False
        assert result[2].is_default is True

    def test_updated_by_and_updated_at_populated_when_tenant_setting_exists(self):
        """テナント設定が存在する場合は updated_at / updated_by がレスポンスに含まれる"""
        features = [make_feature("feature-001", "mfa", default_enabled=False)]
        tenant_settings = [
            make_tenant_setting("tenant-001", "feature-001", "mfa", is_enabled=True)
        ]

        result = merge_tenant_service_features(features, tenant_settings)

        assert result[0].updated_at == datetime(2026, 2, 1)
        assert result[0].updated_by == "admin-user-001"

    def test_updated_by_and_updated_at_none_when_no_tenant_setting(self):
        """テナント設定が存在しない場合は updated_at / updated_by が None で返る"""
        features = [make_feature("feature-001", "mfa", default_enabled=False)]

        result = merge_tenant_service_features(features, tenant_settings=[])

        assert result[0].updated_at is None
        assert result[0].updated_by is None

    def test_empty_features_returns_empty_list(self):
        """機能マスターが空の場合は空リストが返る"""
        result = merge_tenant_service_features(features=[], tenant_settings=[])
        assert result == []
