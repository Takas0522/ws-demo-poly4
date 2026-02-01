"""依存注入の一元管理"""
from fastapi import Depends, Header, HTTPException, Request
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def get_cosmos_container(request: Request):
    """
    Cosmos DBコンテナを取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        Cosmos DBコンテナクライアント
    
    Raises:
        RuntimeError: Cosmos DBが初期化されていない場合
    """
    if not hasattr(request.app.state, "cosmos_container"):
        raise RuntimeError("Cosmos DB not initialized")
    return request.app.state.cosmos_container


def get_request_id(request: Request) -> Optional[str]:
    """
    リクエストIDを取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        リクエストID（存在しない場合はNone）
    """
    return getattr(request.state, "request_id", None)


def get_jwt_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Authorization HeaderからJWTトークンを取得
    
    Args:
        authorization: Authorizationヘッダー
    
    Returns:
        JWTトークン（存在しない場合はNone）
    
    Note:
        実際の認証検証は共通ライブラリのJWT認証ミドルウェアで実施
        この関数はトークン文字列を取得するのみ
    """
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        return authorization[7:]
    
    return None


def get_current_user(request: Request) -> Dict:
    """
    現在のユーザー情報を取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        ユーザー情報辞書（user_id, tenant_id, roles等）
    
    Note:
        Phase 1では仮実装
        共通ライブラリのJWT認証ミドルウェア連携後に実装
    """
    # TODO: JWT認証ミドルウェアからユーザー情報を取得
    # 現在は仮実装（開発・テスト用）
    if hasattr(request.state, "current_user"):
        return request.state.current_user
    
    # デフォルト値（開発環境用）
    return {
        "user_id": "user_admin_001",
        "tenant_id": "tenant_privileged",
        "roles": ["service-setting:administrator"]
    }
