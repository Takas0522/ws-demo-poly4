# Service Settings Service

サービス設定サービス - アプリケーション設定とテナント固有の構成を管理するマイクロサービス

## 🎯 概要

このサービスは、マルチテナント環境でのアプリケーション設定管理を提供します。

### 主な機能

- ✅ 設定CRUD API
- ✅ テナント固有設定の管理
- ✅ 設定検証とスキーマ
- ✅ 設定キャッシング（Redis）
- ✅ 設定継承
- ✅ 構成のバックアップ/リストア機能
- ✅ JWT認証とテナント分離
- ✅ CosmosDB統合

## 🚀 セットアップ

### 前提条件

- Node.js 20.x以上
- Azure CosmosDB アカウント
- Redis サーバー（オプション）

### インストール

```bash
cd src/service-setting-service
npm install
```

### 環境変数設定

`.env.example`を`.env`にコピーして環境変数を設定:

```bash
cp .env.example .env
```

必要な環境変数:
- `COSMOS_ENDPOINT`: CosmosDBエンドポイント
- `COSMOS_KEY`: CosmosDBアクセスキー
- `JWT_SECRET`: JWT署名シークレット
- `REDIS_HOST`: Redisホスト（オプション）

### 開発環境での実行

```bash
npm run dev
```

### ビルド

```bash
npm run build
```

### 本番環境での実行

```bash
npm start
```

## 🐳 Dockerでの実行

```bash
docker-compose up -d
```

## 📚 API エンドポイント

### 認証

すべてのエンドポイントは、`Authorization: Bearer <token>` ヘッダーが必要です。

### 設定管理

#### 設定の作成
```
POST /api/configurations
Content-Type: application/json
Authorization: Bearer <token>

{
  "tenantId": "tenant-123",
  "key": "app.feature.enabled",
  "value": true,
  "description": "Feature flag for new feature",
  "tags": ["feature", "production"]
}
```

#### 設定の取得（ID）
```
GET /api/configurations/:id
Authorization: Bearer <token>
```

#### 設定の取得（キー）
```
GET /api/configurations/key/:key
Authorization: Bearer <token>
```

#### 設定一覧の取得
```
GET /api/configurations?includeInherited=true
Authorization: Bearer <token>
```

#### 設定の更新
```
PUT /api/configurations/:id
Content-Type: application/json
Authorization: Bearer <token>

{
  "value": false,
  "changeReason": "Disable feature for maintenance"
}
```

#### 設定の削除
```
DELETE /api/configurations/:id
Authorization: Bearer <token>
```

### バックアップ/リストア

#### バックアップの作成
```
POST /api/configurations/backup
Content-Type: application/json
Authorization: Bearer <token>

{
  "description": "Daily backup"
}
```

#### バックアップのリストア
```
POST /api/configurations/restore/:backupId
Authorization: Bearer <token>
```

### ヘルスチェック

```
GET /api/health
```

## 🧪 テスト

```bash
# すべてのテストを実行
npm test

# ウォッチモード
npm run test:watch

# カバレッジ
npm run test:coverage
```

## 🔧 開発

### リント

```bash
npm run lint
npm run lint:fix
```

## 🏗️ アーキテクチャ

```
src/
├── config/           # アプリケーション設定
├── controllers/      # リクエストハンドラー
├── middleware/       # Express ミドルウェア
├── repositories/     # データアクセス層
├── routes/           # APIルート定義
├── services/         # ビジネスロジック
├── types/            # TypeScript型定義
├── utils/            # ユーティリティ関数
├── validators/       # バリデーションスキーマ
├── app.ts            # アプリケーション設定
└── index.ts          # エントリーポイント
```

## 🔐 セキュリティ

- JWT認証による保護
- テナント分離の実装
- 入力バリデーション
- エラーハンドリング

## 📝 ライセンス

MIT
