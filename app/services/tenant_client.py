"""テナント管理サービスクライアント"""
import logging
import httpx
from typing import Optional

from app.config import settings
from app.utils.validators import validate_https_url

logger = logging.getLogger(__name__)


class TenantClient:
    """テナント管理サービスAPIクライアント"""

    def __init__(self):
        """TenantClientを初期化"""
        self.base_url = settings.TENANT_SERVICE_BASE_URL
        self.timeout = 1.0  # 1秒タイムアウト
        self.logger = logger
        
        # 本番環境ではHTTPS検証
        try:
            validate_https_url(self.base_url, settings.is_production)
        except ValueError as e:
            self.logger.error(f"Tenant service URL validation failed: {e}")
            raise

    async def verify_tenant_exists(self, tenant_id: str, jwt_token: str) -> bool:
        """
        テナント存在確認
        
        Args:
            tenant_id: テナントID
            jwt_token: JWT認証トークン
        
        Returns:
            bool: テナントが存在する場合はTrue、存在しない場合はFalse
        
        Raises:
            httpx.TimeoutException: タイムアウトした場合
            httpx.HTTPStatusError: サービスが利用不可の場合
        
        Note:
            テナント管理サービスの GET /api/v1/tenants/{tenantId} を呼び出し、
            200ステータスを確認します。
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    self.logger.info(f"Tenant verified: {tenant_id}")
                    return True
                elif response.status_code == 404:
                    self.logger.warning(f"Tenant not found: {tenant_id}")
                    return False
                else:
                    # その他のエラー（401, 403, 503など）
                    self.logger.error(
                        f"Failed to verify tenant {tenant_id}: HTTP {response.status_code}",
                        extra={
                            "tenant_id": tenant_id,
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                    raise httpx.HTTPStatusError(
                        f"Tenant service returned {response.status_code}",
                        request=response.request,
                        response=response
                    )
        
        except httpx.TimeoutException as e:
            self.logger.error(
                f"Timeout verifying tenant {tenant_id}",
                extra={"tenant_id": tenant_id, "timeout": self.timeout}
            )
            raise
        
        except httpx.RequestError as e:
            self.logger.error(
                f"Request error verifying tenant {tenant_id}: {e}",
                extra={"tenant_id": tenant_id, "error": str(e)}
            )
            raise

    async def get_tenant(
        self, tenant_id: str, jwt_token: str
    ) -> Optional[dict]:
        """
        テナント情報取得
        
        Args:
            tenant_id: テナントID
            jwt_token: JWT認証トークン
        
        Returns:
            Optional[dict]: テナント情報、存在しない場合はNone
        
        Raises:
            httpx.TimeoutException: タイムアウトした場合
            httpx.HTTPStatusError: サービスが利用不可の場合
        
        Note:
            現在のPhaseでは使用されませんが、将来的な拡張のために提供
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    tenant_data = response.json()
                    self.logger.info(f"Tenant retrieved: {tenant_id}")
                    return tenant_data
                elif response.status_code == 404:
                    self.logger.warning(f"Tenant not found: {tenant_id}")
                    return None
                else:
                    self.logger.error(
                        f"Failed to get tenant {tenant_id}: HTTP {response.status_code}",
                        extra={
                            "tenant_id": tenant_id,
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                    raise httpx.HTTPStatusError(
                        f"Tenant service returned {response.status_code}",
                        request=response.request,
                        response=response
                    )
        
        except httpx.TimeoutException as e:
            self.logger.error(
                f"Timeout getting tenant {tenant_id}",
                extra={"tenant_id": tenant_id, "timeout": self.timeout}
            )
            raise
        
        except httpx.RequestError as e:
            self.logger.error(
                f"Request error getting tenant {tenant_id}: {e}",
                extra={"tenant_id": tenant_id, "error": str(e)}
            )
            raise
