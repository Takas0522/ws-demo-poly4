# テナント管理サービス (Tenant Management Service)

## 概要

本サービスは、テナント（組織）とテナント所属ユーザーを管理するマイクロサービスです。  
マルチテナントアーキテクチャの中核を担い、テナントのライフサイクル管理と特権テナントの保護機能を提供します。

## 技術スタック

- **フレームワーク**: FastAPI
- **言語**: Python 3.11+
- **データベース**: Azure Cosmos DB (NoSQL API)
- **バリデーション**: Pydantic
- **認証**: JWT (JSON Web Token)

## ディレクトリ構造

```
src/tenant-management-service/
├── app/
│   ├── main.py              # FastAPIアプリケーションエントリーポイント
│   ├── api/                 # APIエンドポイント
│   │   └── v1/
│   │       ├── tenants.py   # テナント管理エンドポイント
│   │       └── tenant_users.py # テナントユーザー管理
│   ├── models/              # データモデル（Pydantic）
│   │   ├── tenant.py
│   │   └── tenant_user.py
│   ├── repositories/        # データアクセス層
│   │   ├── tenant_repository.py
│   │   └── tenant_user_repository.py
│   ├── services/            # ビジネスロジック層
│   │   ├── tenant_service.py
│   │   └── tenant_user_service.py
│   ├── core/                # コア機能
│   │   ├── config.py        # 設定管理
│   │   ├── database.py      # DB接続管理
│   │   └── dependencies.py  # 依存性注入
│   └── utils/               # ユーティリティ
│       ├── logger.py
│       └── exceptions.py
├── tests/                   # テストコード
│   ├── unit/
│   └── integration/
├── .env                     # 環境変数
├── requirements.txt         # Python依存関係
├── Dockerfile              # Dockerイメージ定義
└── README.md               # このファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成：

```bash
# Cosmos DB
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=your-cosmos-key
COSMOS_DATABASE_NAME=tenant_management

# Application
APP_NAME=Tenant Management Service
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Auth Service (ユーザー情報取得用)
AUTH_SERVICE_URL=http://localhost:8001
```

### 3. データベースの初期化

```bash
python -m app.scripts.init_db
```

### 4. サービスの起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

API ドキュメント: http://localhost:8002/docs

## 開発

### 新しいエンドポイントの追加

1. **モデル定義** (`app/models/`)
```python
# app/models/tenant.py
from pydantic import BaseModel
from typing import List

class TenantCreate(BaseModel):
    name: str
    domains: List[str]
```

2. **リポジトリ実装** (`app/repositories/`)
```python
# app/repositories/tenant_repository.py
class TenantRepository:
    async def create(self, tenant: TenantCreate) -> Tenant:
        # Cosmos DB への書き込み
        pass
```

3. **サービス実装** (`app/services/`)
```python
# app/services/tenant_service.py
class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo
    
    async def create_tenant(self, tenant: TenantCreate) -> Tenant:
        # 特権テナントのチェック
        # ビジネスロジック
        return await self.tenant_repo.create(tenant)
```

4. **エンドポイント実装** (`app/api/v1/`)
```python
# app/api/v1/tenants.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/tenants", response_model=Tenant)
async def create_tenant(
    tenant: TenantCreate,
    service: TenantService = Depends(get_tenant_service)
):
    return await service.create_tenant(tenant)
```

### 認証の追加

JWT認証が必要なエンドポイント：

```python
from app.core.dependencies import get_current_user

@router.get("/tenants")
async def list_tenants(
    current_user: User = Depends(get_current_user)
):
    # 認証済みユーザーのみアクセス可能
    pass
```

### ロールベースアクセス制御

```python
from app.core.dependencies import require_role

@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(require_role("管理者"))
):
    # 管理者のみアクセス可能
    pass
```

## テスト

### ユニットテスト

```bash
pytest tests/unit/
```

### 統合テスト

```bash
pytest tests/integration/
```

### カバレッジ

```bash
pytest --cov=app tests/
```

## API エンドポイント

### テナント管理

#### テナント一覧取得
```http
GET /api/v1/tenants?page=1&limit=20
Authorization: Bearer {token}
```

**レスポンス**:
```json
{
  "items": [
    {
      "id": "tenant-uuid",
      "name": "株式会社サンプル",
      "domains": ["example.com"],
      "is_privileged": false,
      "user_count": 10,
      "service_count": 3,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

#### テナント詳細取得
```http
GET /api/v1/tenants/{tenant_id}
Authorization: Bearer {token}
```

#### テナント作成
```http
POST /api/v1/tenants
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "新規テナント",
  "domains": ["newtenant.com"]
}
```

#### テナント更新
```http
PUT /api/v1/tenants/{tenant_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "更新後のテナント名",
  "domains": ["updated.com", "newtenant.com"]
}
```

#### テナント削除
```http
DELETE /api/v1/tenants/{tenant_id}
Authorization: Bearer {token}
```

**注意**: 特権テナントは削除できません

### テナントユーザー管理

#### テナントユーザー一覧取得
```http
GET /api/v1/tenants/{tenant_id}/users
Authorization: Bearer {token}
```

#### ユーザーをテナントに追加
```http
POST /api/v1/tenant-users
Authorization: Bearer {token}
Content-Type: application/json

{
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid"
}
```

#### テナントからユーザーを削除
```http
DELETE /api/v1/tenant-users/{tenant_user_id}
Authorization: Bearer {token}
```

詳細は [API設計仕様書](../../docs/arch/api/api-specification.md#3-テナント管理サービス-api) を参照してください。

## データモデル

### Tenant

```json
{
  "id": "tenant-uuid",
  "type": "tenant",
  "name": "株式会社サンプル",
  "domains": ["example.com", "sample.co.jp"],
  "is_privileged": false,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "partition_key": "tenant-uuid"
}
```

### TenantUser

```json
{
  "id": "tenant-user-uuid",
  "type": "tenant_user",
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid",
  "created_at": "2024-01-15T10:00:00Z",
  "partition_key": "tenant-uuid"
}
```

詳細は [データ設計](../../docs/arch/data/data-model.md#21-テナント管理データモデル) を参照してください。

## ビジネスルール

### 特権テナント

特権テナント（`is_privileged: true`）には以下の制約があります：

1. **削除不可**: 特権テナントは削除できません
2. **編集制限**: テナント名とドメインの編集は「全体管理者」ロールのみ可能
3. **ユーザー管理**: ユーザーの追加・削除は「全体管理者」ロールのみ可能
4. **システム内に1つのみ**: 複数の特権テナントは作成できません

### ドメイン管理

- ドメインは複数指定可能
- 同じドメインを複数のテナントに割り当てることはできません
- ドメインの追加・削除時にバリデーションを実施

### ユーザー追加

- ユーザーは認証認可サービスで管理されている必要があります
- 1人のユーザーは複数のテナントに所属できます
- ユーザー追加時に、認証認可サービスからユーザー情報を取得して検証

## トラブルシューティング

### Q: Cosmos DB に接続できない

```bash
# 接続文字列を確認
echo $COSMOS_ENDPOINT
echo $COSMOS_KEY

# Cosmos DB Emulator が起動しているか確認
docker ps | grep cosmos
```

### Q: 認証サービスと連携できない

```bash
# 認証サービスのURLを確認
echo $AUTH_SERVICE_URL

# 認証サービスが起動しているか確認
curl http://localhost:8001/health
```

### Q: 特権テナントが削除できない

- 特権テナント（`is_privileged: true`）は仕様により削除できません
- 削除が必要な場合は、データベースを直接操作してください（開発環境のみ）

## 関連ドキュメント

- [コンポーネント設計 - テナント管理サービス](../../docs/arch/components/README.md#3-テナント管理サービス)
- [API設計仕様書](../../docs/arch/api/api-specification.md#3-テナント管理サービス-api)
- [データ設計](../../docs/arch/data/data-model.md#21-テナント管理データモデル)
- [アーキテクチャ概要](../../docs/arch/overview.md)

## ライセンス

MIT License
