# ws-demo-poly4

Service Settings Service - サービス設定サービス

## 概要

アプリケーション設定とテナント固有の構成を管理するマイクロサービス。

## サービス

- **service-setting-service**: 設定CRUD、テナント固有設定、設定継承、バックアップ/リストア機能を提供

## セットアップ

```bash
cd src/service-setting-service
npm install
npm run dev
```

詳細は [service-setting-service/README.md](src/service-setting-service/README.md) を参照してください。