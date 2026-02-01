# Service Setting Service

マルチテナント管理アプリケーションのサービス設定サービスです。

## 技術スタック

- **フレームワーク**: FastAPI 0.109.2
- **言語**: Python 3.11+
- **データベース**: Azure Cosmos DB
- **認証**: JWT

## セットアップ

### 環境変数

```bash
SERVICE_NAME=service-setting-service
ENVIRONMENT=development
LOG_LEVEL=INFO
API_VERSION=v1

COSMOS_DB_CONNECTION_STRING=<your-cosmos-db-connection-string>
COSMOS_DB_DATABASE_NAME=management-app
COSMOS_DB_CONTAINER_NAME=service_setting

JWT_SECRET_KEY=<your-jwt-secret-key>
JWT_ALGORITHM=HS256

APPINSIGHTS_INSTRUMENTATIONKEY=<your-app-insights-key>
ALLOWED_ORIGINS=http://localhost:3000
```

### インストール

```bash
pip install -r requirements.txt
```

### 起動

```bash
python -m app.main
# または
uvicorn app.main:app --reload --port 8002
```

## テスト

```bash
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=html
```
