"""サービスカタログ管理サービス"""
from typing import List, Optional
import logging

from app.models.service import Service
from app.repositories.service_repository import ServiceRepository

logger = logging.getLogger(__name__)


class ServiceService:
    """サービスカタログ管理サービス"""

    def __init__(self, service_repository: ServiceRepository):
        """
        ServiceServiceを初期化
        
        Args:
            service_repository: サービスリポジトリ
        """
        self.service_repository = service_repository
        self.logger = logger

    async def get_service(self, service_id: str) -> Optional[Service]:
        """
        サービス詳細取得
        
        Args:
            service_id: サービスID
        
        Returns:
            Optional[Service]: サービスが存在する場合はServiceインスタンス、存在しない場合はNone
        """
        service = await self.service_repository.get_service(service_id)
        
        if service:
            self.logger.info(f"Service retrieved: {service_id}")
        else:
            self.logger.warning(f"Service not found: {service_id}")
        
        return service

    async def list_services(self, is_active: bool = True) -> List[Service]:
        """
        サービス一覧取得
        
        Args:
            is_active: アクティブ状態フィルタ（Trueの場合はアクティブなサービスのみ）
        
        Returns:
            List[Service]: サービス一覧
        
        Note:
            全サービスは _system パーティションに格納されているため、
            単一パーティションクエリで高速に取得可能（< 200ms）
        """
        services = await self.service_repository.list_all(is_active=is_active)
        
        self.logger.info(
            f"Services listed: {len(services)} services (is_active={is_active})",
            extra={"service_count": len(services), "is_active": is_active}
        )
        
        return services

    async def create_service(self, service: Service, created_by: str) -> Service:
        """
        サービス作成（管理用）
        
        Args:
            service: 作成するサービス
            created_by: 作成者ユーザーID
        
        Returns:
            Service: 作成されたサービス
        
        Raises:
            ValueError: サービスIDが重複している場合
        
        Note:
            Phase 1ではAPIで提供せず、データベース直接操作またはスクリプトで実行
        """
        # サービスIDの重複チェック
        existing = await self.service_repository.get_service(service.id)
        if existing:
            raise ValueError(f"Service '{service.id}' already exists")
        
        # サービス作成
        created_service = await self.service_repository.create_service(service)
        
        self.logger.info(
            f"Service created: {created_service.id} by {created_by}",
            extra={"service_id": created_service.id, "created_by": created_by}
        )
        
        return created_service

    async def update_service(
        self,
        service_id: str,
        update_data: dict,
        updated_by: str
    ) -> Service:
        """
        サービス更新（管理用）
        
        Args:
            service_id: サービスID
            update_data: 更新データ
            updated_by: 更新者ユーザーID
        
        Returns:
            Service: 更新されたサービス
        
        Raises:
            ValueError: サービスが存在しない場合
        
        Note:
            Phase 1ではAPIで提供せず、データベース直接操作またはスクリプトで実行
        """
        # サービス存在確認
        existing = await self.service_repository.get_service(service_id)
        if not existing:
            raise ValueError(f"Service '{service_id}' not found")
        
        # 更新データに updated_by を追加
        update_data["updated_by"] = updated_by
        
        # サービス更新
        updated_service = await self.service_repository.update_service(
            service_id, update_data
        )
        
        self.logger.info(
            f"Service updated: {service_id} by {updated_by}",
            extra={"service_id": service_id, "updated_by": updated_by}
        )
        
        return updated_service

    async def delete_service(self, service_id: str, deleted_by: str) -> None:
        """
        サービス削除（管理用）
        
        Args:
            service_id: サービスID
            deleted_by: 削除者ユーザーID
        
        Raises:
            ValueError: サービスが存在しない場合
        
        Note:
            Phase 1ではAPIで提供せず、データベース直接操作またはスクリプトで実行
        """
        # サービス存在確認
        existing = await self.service_repository.get_service(service_id)
        if not existing:
            raise ValueError(f"Service '{service_id}' not found")
        
        # サービス削除
        await self.service_repository.delete_service(service_id)
        
        self.logger.info(
            f"Service deleted: {service_id} by {deleted_by}",
            extra={"service_id": service_id, "deleted_by": deleted_by}
        )

    async def count_active_services(self) -> int:
        """
        アクティブなサービス数を取得
        
        Returns:
            int: アクティブなサービス数
        """
        count = await self.service_repository.count_active_services()
        return count
