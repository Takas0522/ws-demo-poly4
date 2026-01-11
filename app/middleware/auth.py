from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from app.core.config import settings
from app.core.logger import logger
from app.models.auth import JWTPayload

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials) -> JWTPayload:
    """Verify JWT token and return payload"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], issuer=settings.JWT_ISSUER
        )
        return JWTPayload(**payload)
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> JWTPayload:
    """Dependency to get current authenticated user"""
    return await verify_token(credentials)
