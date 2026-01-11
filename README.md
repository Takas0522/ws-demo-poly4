# ws-demo-poly4

Service Settings Service - サービス設定サービス

## 概要

アプリケーション設定とテナント固有の構成を管理するマイクロサービス（FastAPI Python実装）。

## サービス

- **service-setting-service**: 設定CRUD、テナント固有設定、設定継承、バックアップ/リストア機能を提供

## セットアップ

```bash
cd src/service-setting-service

# 仮想環境の作成
python -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# サービスの起動
uvicorn app.main:app --reload
```

詳細は [service-setting-service/README.md](src/service-setting-service/README.md) を参照してください。