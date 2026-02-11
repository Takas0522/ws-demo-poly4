# テナント管理サービス API 仕様書

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft
- **共通仕様**: [共通API仕様](../../../docs/arch/api/api-specification.md) を参照

---

## 概要

**ベースURL**: `http://localhost:8002/api/v1`

テナント管理サービスは、テナントとテナント所属ユーザーのライフサイクル管理を行います。

---

## 1. テナント管理エンドポイント

### 1.1 テナント一覧取得

```http
GET /tenants?page=1&per_page=20
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "data": [
    {
      "id": "tenant-uuid",
      "name": "株式会社サンプル",
      "domains": ["example.com"],
      "is_privileged": false,
      "user_count": 25,
      "service_count": 4,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15,
    "total_pages": 1
  }
}
```

### 1.2 テナント詳細取得

```http
GET /tenants/{tenant_id}
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "id": "tenant-uuid",
  "name": "株式会社サンプル",
  "domains": ["example.com", "sample.co.jp"],
  "is_privileged": false,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "users": [
    {
      "id": "user-uuid",
      "user_id": "user@example.com",
      "name": "山田太郎"
    }
  ],
  "services": [
    {
      "id": "service-uuid",
      "name": "ファイル管理サービス",
      "assigned_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 1.3 テナント作成

```http
POST /tenants
Authorization: Bearer {token}
```

**必要ロール**: 管理者以上

**リクエスト**:

```json
{
  "name": "株式会社新規",
  "domains": ["newcompany.com"]
}
```

**レスポンス** (201):

```json
{
  "id": "tenant-uuid",
  "name": "株式会社新規",
  "domains": ["newcompany.com"],
  "is_privileged": false,
  "created_at": "2024-01-25T10:00:00Z"
}
```

**エラー** (409):

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Tenant name already exists"
  }
}
```

### 1.4 テナント更新

```http
PUT /tenants/{tenant_id}
Authorization: Bearer {token}
```

**必要ロール**: 管理者以上

**リクエスト**:

```json
{
  "name": "株式会社更新後",
  "domains": ["updated.com"]
}
```

**レスポンス** (200):

```json
{
  "id": "tenant-uuid",
  "name": "株式会社更新後",
  "domains": ["updated.com"],
  "is_privileged": false,
  "updated_at": "2024-01-25T11:00:00Z"
}
```

**エラー** (403):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Cannot edit privileged tenant"
  }
}
```

### 1.5 テナント削除

```http
DELETE /tenants/{tenant_id}
Authorization: Bearer {token}
```

**必要ロール**: 管理者以上

**レスポンス** (204): No Content

**エラー** (403):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Cannot delete privileged tenant"
  }
}
```

---

## 2. テナントユーザー管理エンドポイント

### 2.1 テナント所属ユーザー取得

```http
GET /tenants/{tenant_id}/users
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "tenant_id": "tenant-uuid",
  "users": [
    {
      "id": "user-uuid",
      "user_id": "user@example.com",
      "name": "山田太郎",
      "added_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 2.2 テナントにユーザー追加

```http
POST /tenants/{tenant_id}/users
Authorization: Bearer {token}
```

**必要ロール**: 管理者以上（特権テナントの場合は全体管理者のみ）

**リクエスト**:

```json
{
  "user_id": "user-uuid"
}
```

**レスポンス** (201):

```json
{
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid",
  "added_at": "2024-01-25T10:00:00Z"
}
```

**エラー** (403):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Only global admin can modify privileged tenant users"
  }
}
```

### 2.3 テナントからユーザー削除

```http
DELETE /tenants/{tenant_id}/users/{user_id}
Authorization: Bearer {token}
```

**必要ロール**: 管理者以上（特権テナントの場合は全体管理者のみ）

**レスポンス** (204): No Content

---

## エンドポイント一覧

| メソッド | エンドポイント                                | 説明                 | 必要ロール |
| -------- | --------------------------------------------- | -------------------- | ---------- |
| GET      | `/api/v1/tenants`                             | テナント一覧         | 閲覧者以上 |
| GET      | `/api/v1/tenants/{tenant_id}`                 | テナント詳細         | 閲覧者以上 |
| POST     | `/api/v1/tenants`                             | テナント作成         | 管理者以上 |
| PUT      | `/api/v1/tenants/{tenant_id}`                 | テナント更新         | 管理者以上 |
| DELETE   | `/api/v1/tenants/{tenant_id}`                 | テナント削除         | 管理者以上 |
| GET      | `/api/v1/tenants/{tenant_id}/users`           | テナント所属ユーザー | 閲覧者以上 |
| POST     | `/api/v1/tenants/{tenant_id}/users`           | ユーザー追加         | 管理者以上 |
| DELETE   | `/api/v1/tenants/{tenant_id}/users/{user_id}` | ユーザー削除         | 管理者以上 |

---

## 変更履歴

| バージョン | 日付 | 変更内容                                | 作成者             |
| ---------- | ---- | --------------------------------------- | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合APIドキュメントから分離） | Architecture Agent |
