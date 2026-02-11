"""JWT トークン検証（認証サービスと共通）"""
from jose import jwt, JWTError
from typing import Dict, Optional
from ..config import get_settings

settings = get_settings()


def verify_jwt_token(token: str) -> Optional[Dict]:
    """JWT検証"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
