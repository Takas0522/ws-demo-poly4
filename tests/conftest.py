"""pytest共通フィクスチャ"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any


class AsyncIteratorMock:
    """非同期イテレータのモック"""
    
    def __init__(self, items: list):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.fixture
def mock_cosmos_container():
    """Cosmos DBコンテナモック"""
    container = MagicMock()
    
    # in-memoryストレージ（テスト用データベース）
    storage: Dict[str, Any] = {}
    
    async def mock_read_item(item: str, partition_key: str):
        key = f"{partition_key}:{item}"
        if key in storage:
            return storage[key]
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        raise CosmosResourceNotFoundError(status_code=404, message="Item not found")
    
    async def mock_create_item(body: dict):
        key = f"{body['tenant_id']}:{body['id']}"
        if key in storage:
            from azure.cosmos.exceptions import CosmosResourceExistsError
            raise CosmosResourceExistsError(status_code=409, message="Item already exists")
        storage[key] = body
        return body
    
    async def mock_upsert_item(body: dict):
        key = f"{body['tenant_id']}:{body['id']}"
        storage[key] = body
        return body
    
    async def mock_delete_item(item: str, partition_key: str):
        key = f"{partition_key}:{item}"
        if key in storage:
            del storage[key]
        else:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError
            raise CosmosResourceNotFoundError(status_code=404, message="Item not found")
    
    def mock_query_items(query: str, parameters=None, partition_key=None, enable_cross_partition_query=False):
        items = []
        # Check if this is a COUNT query
        if "COUNT" in query.upper():
            # Return a simple integer count
            count = 0
            for key, item in storage.items():
                if partition_key and item.get('tenant_id') != partition_key:
                    continue
                # Apply basic filtering based on query
                if "type = 'service'" in query and item.get('type') == 'service':
                    if "is_active = true" in query and item.get('is_active') == True:
                        count += 1
                    elif "is_active" not in query:
                        count += 1
                elif "type = 'service_assignment'" in query and item.get('type') == 'service_assignment':
                    count += 1
            return AsyncIteratorMock([count])
        
        # Regular query - return full items
        for key, item in storage.items():
            if partition_key and item.get('tenant_id') != partition_key:
                continue
            items.append(item)
        return AsyncIteratorMock(items)
    
    container.read_item = mock_read_item
    container.create_item = mock_create_item
    container.upsert_item = mock_upsert_item
    container.delete_item = mock_delete_item
    container.query_items = mock_query_items
    container._storage = storage  # テスト用にストレージを公開
    
    return container


@pytest.fixture
def mock_tenant_client():
    """TenantClientモック"""
    client = AsyncMock()
    
    # デフォルトでテナント存在確認は成功
    client.verify_tenant_exists.return_value = True
    
    return client


@pytest.fixture
def test_service_file():
    """テスト用Serviceデータ（file-service）"""
    return {
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
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def test_service_inactive():
    """テスト用Serviceデータ（非アクティブ）"""
    return {
        "id": "inactive-service",
        "tenant_id": "_system",
        "type": "service",
        "name": "非アクティブサービス",
        "description": "テスト用非アクティブサービス",
        "version": "1.0.0",
        "is_active": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def test_assignment():
    """テスト用ServiceAssignmentデータ"""
    return {
        "id": "assignment_tenant_acme_file-service",
        "tenant_id": "tenant_acme",
        "type": "service_assignment",
        "service_id": "file-service",
        "status": "active",
        "config": {
            "max_storage": "100GB",
            "max_file_size": "10MB"
        },
        "assigned_at": datetime.utcnow(),
        "assigned_by": "user_admin_001"
    }


@pytest.fixture
def large_config_dict():
    """大きなconfigデータ生成（サイズ検証用）"""
    def _generate(size_bytes: int) -> dict:
        # サイズを増やすために大きな文字列を含むconfigを生成
        base_size = 100
        num_keys = size_bytes // base_size
        config = {}
        for i in range(num_keys):
            config[f"key_{i}"] = "x" * base_size
        return config
    return _generate


@pytest.fixture
def nested_config_dict():
    """ネストされたconfigデータ生成（ネストレベル検証用）"""
    def _generate(depth: int) -> dict:
        # 指定された深さまでネストしたconfigを生成
        if depth <= 0:
            return {"value": "leaf"}
        return {"nested": _generate(depth - 1)}
    return _generate
