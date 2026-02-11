# テナント管理サービス コンポーネント設計

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft

---

## 1. 概要

テナント（企業）情報の管理とテナント所属ユーザーの管理を担当するマイクロサービスです。

## 2. ディレクトリ構造

```
src/tenant-management-service/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── config.py               # 設定管理
│   ├── models/                 # データモデル
│   │   └── tenant.py
│   ├── schemas/                # Pydanticスキーマ
│   │   └── tenant.py
│   ├── repositories/           # データアクセス層
│   │   └── tenant_repository.py
│   ├── services/               # ビジネスロジック
│   │   └── tenant_service.py
│   ├── api/                    # APIエンドポイント
│   │   └── v1/
│   │       └── tenants.py
│   └── utils/                  # ユーティリティ
│       └── dependencies.py
├── tests/
├── infra/                      # IaC定義
│   └── container-app.bicep
├── Dockerfile
└── requirements.txt
```

## 3. 主要機能

### 3.1 テナントCRUD

**テナント作成**

```python
class TenantService:
    async def create_tenant(self, data: TenantCreate) -> Tenant:
        tenant = Tenant(
            id=generate_uuid(),
            tenant_name=data.tenant_name,
            display_name=data.display_name,
            is_active=True,
            is_privileged=data.is_privileged or False,
            created_at=datetime.utcnow()
        )

        await self.tenant_repo.create(tenant)
        return tenant
```

**テナント取得**

```python
class TenantService:
    async def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    async def list_tenants(
        self,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedResponse[Tenant]:
        return await self.tenant_repo.list_with_pagination(page, per_page)
```

### 3.2 テナントユーザー管理

**テナントへのユーザー追加**

```python
class TenantService:
    async def add_user_to_tenant(
        self,
        tenant_id: str,
        user_data: TenantUserCreate
    ) -> TenantUser:
        # テナント存在確認
        tenant = await self.get_tenant(tenant_id)

        # ユーザー追加
        user = TenantUser(
            id=generate_uuid(),
            user_name=user_data.user_name,
            email=user_data.email,
            tenant_id=tenant_id,
            is_active=True,
            created_at=datetime.utcnow()
        )

        await self.tenant_repo.add_user(user)
        return user
```

### 3.3 特権テナント管理

```python
class TenantService:
    async def get_privileged_tenant(self) -> Optional[Tenant]:
        """特権テナント（SaaS管理者用）を取得"""
        tenants = await self.tenant_repo.find_by_condition(
            {"is_privileged": True}
        )
        return tenants[0] if tenants else None
```

## 4. データモデル

```python
class Tenant(BaseModel):
    id: str
    tenant_name: str
    display_name: str
    is_active: bool = True
    is_privileged: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class TenantUser(BaseModel):
    id: str
    user_name: str
    email: Optional[str] = None
    tenant_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
```

データベース詳細は [データ設計](../../../docs/arch/data/data-model.md) を参照してください。

## 5. 環境変数

```bash
# Database
COSMOS_DB_ENDPOINT=https://xxx.documents.azure.com:443/
COSMOS_DB_KEY=xxx
COSMOS_DB_DATABASE=tenant_management

# Service
SERVICE_NAME=tenant-management-service
PORT=8002
```

---

## 変更履歴

| バージョン | 日付 | 変更内容                                   | 作成者             |
| ---------- | ---- | ------------------------------------------ | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合コンポーネント設計から分離） | Architecture Agent |
