# Service Settings Service

Service Settings Service - サービス設定サービス (FastAPI Python implementation)

## 🎯 概要

このサービスは、マルチテナント環境でのアプリケーション設定管理を提供します。

### 主な機能

- ✅ 設定 CRUD API
- ✅ テナント固有設定の管理
- ✅ 設定検証とスキーマ
- ✅ 設定キャッシング（Redis）
- ✅ 設定継承
- ✅ 構成のバックアップ/リストア機能
- ✅ JWT 認証とテナント分離
- ✅ CosmosDB 統合
- **Default Port**: 3003

## 🚀 セットアップ

### 前提条件

- Python 3.11 以上
- Azure CosmosDB アカウント
- Redis サーバー（オプション）

### インストール

```bash
cd src/service-setting-service

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開発環境用
```

### 環境変数設定

`.env.example`を`.env`にコピーして環境変数を設定:

```bash
cp .env.example .env
```

必要な環境変数:

- `PORT`: サービスポート (デフォルト: 3003)
- `COSMOS_ENDPOINT`: CosmosDB エンドポイント
- `COSMOS_KEY`: CosmosDB アクセスキー
- `JWT_SECRET`: JWT 署名シークレット
- `REDIS_HOST`: Redis ホスト（オプション）

### 開発環境での実行

```bash
# Uvicornで起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 3003

# または
python -m app.main
```

## 🐳 Docker での実行

```bash
docker-compose up -d
```

## 📚 API エンドポイント

### 認証

すべてのエンドポイントは、`Authorization: Bearer <token>` ヘッダーが必要です。

### 設定管理

#### 設定の作成

```http
POST /api/configurations
Content-Type: application/json
Authorization: Bearer <token>

{
  "tenant_id": "tenant-123",
  "key": "app.feature.enabled",
  "value": true,
  "description": "Feature flag for new feature",
  "tags": ["feature", "production"]
}
```

#### 設定の取得（ID）

```http
GET /api/configurations/{id}
Authorization: Bearer <token>
```

#### 設定の取得（キー）

```http
GET /api/configurations/key/{key}
Authorization: Bearer <token>
```

#### 設定一覧の取得

```http
GET /api/configurations?include_inherited=true
Authorization: Bearer <token>
```

#### 設定の更新

```http
PUT /api/configurations/{id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "value": false,
  "change_reason": "Disable feature for maintenance"
}
```

#### 設定の削除

```http
DELETE /api/configurations/{id}
Authorization: Bearer <token>
```

### バックアップ/リストア

#### バックアップの作成

```http
POST /api/configurations/backup
Content-Type: application/json
Authorization: Bearer <token>

{
  "description": "Daily backup"
}
```

#### バックアップのリストア

```http
POST /api/configurations/restore/{backup_id}
Authorization: Bearer <token>
```

### ヘルスチェック

```http
GET /api/health
```

### API ドキュメント

サービスを起動後、以下の URL で API ドキュメントにアクセスできます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 テスト

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=app --cov-report=html

# 特定のテストファイルを実行
pytest tests/test_configuration_service.py
```

## 🔧 開発

### コードフォーマット

```bash
# Black でフォーマット
black app tests

# Flake8 でリント
flake8 app tests

# MyPy で型チェック
mypy app
```

## 🏗️ アーキテクチャ

```
app/
├── core/              # アプリケーション設定とロガー
├── models/            # Pydantic モデル
├── middleware/        # 認証とテナント分離
├── repositories/      # データアクセス層（CosmosDB, Redis）
├── services/          # ビジネスロジック
├── routes/            # FastAPI ルート定義
└── main.py            # アプリケーションエントリーポイント
```

## 🔐 セキュリティ

- JWT 認証による保護
- テナント分離の実装
- Pydantic による入力バリデーション
- FastAPI の自動エラーハンドリング

## 📝 ライセンス

MIT
