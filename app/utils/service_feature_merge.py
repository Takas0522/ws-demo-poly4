"""サービス機能マージロジック"""
from typing import List, Optional
from ..models.service_feature import ServiceFeature, TenantServiceFeature
from ..schemas.service_feature import TenantServiceFeatureResponse


def merge_tenant_service_features(
    features: List[ServiceFeature],
    tenant_settings: List[TenantServiceFeature],
) -> List[TenantServiceFeatureResponse]:
    """ServiceFeature マスターとテナント別設定をマージして返す。

    テナント設定が存在しない機能は ServiceFeature.default_enabled が適用される。

    Args:
        features: ServiceFeature マスターのリスト
        tenant_settings: テナント別機能設定のリスト（存在しない場合は空リスト）

    Returns:
        マージ済みのテナント別機能設定レスポンスリスト
    """
    tenant_map = {ts.feature_id: ts for ts in tenant_settings}

    result: List[TenantServiceFeatureResponse] = []
    for feature in features:
        tenant_setting: Optional[TenantServiceFeature] = tenant_map.get(feature.id)
        result.append(
            TenantServiceFeatureResponse(
                feature_id=feature.id,
                service_id=feature.service_id,
                feature_key=feature.feature_key,
                feature_name=feature.feature_name,
                description=feature.description,
                is_enabled=(
                    tenant_setting.is_enabled
                    if tenant_setting is not None
                    else feature.default_enabled
                ),
                is_default=tenant_setting is None,
                updated_at=tenant_setting.updated_at if tenant_setting else None,
                updated_by=tenant_setting.updated_by if tenant_setting else None,
            )
        )
    return result
