"""Authentication and authorization utilities."""
import logging
from typing import Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer token
security = HTTPBearer()

# Cache for the public key
_public_key_cache: Optional[str] = None


async def get_auth_public_key() -> str:
    """
    Fetch the public key from Auth Service for JWT verification.
    
    Returns:
        str: The public key in PEM format.
        
    Raises:
        HTTPException: If unable to fetch the public key.
    """
    global _public_key_cache
    
    # Return cached key if available
    if _public_key_cache:
        return _public_key_cache
    
    try:
        url = f"{settings.auth_service_url}{settings.auth_service_public_key_endpoint}"
        logger.info(f"Fetching public key from {url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            public_key = data.get("publicKey")
            
            if not public_key:
                raise ValueError("Public key not found in response")
            
            # Cache the public key
            _public_key_cache = public_key
            logger.info("Public key fetched and cached successfully")
            
            return public_key
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch public key from Auth Service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to authentication service",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


def clear_public_key_cache() -> None:
    """Clear the cached public key. Useful for testing or key rotation."""
    global _public_key_cache
    _public_key_cache = None
    logger.info("Public key cache cleared")


class CurrentUser:
    """Represents the authenticated user from JWT token."""
    
    def __init__(self, payload: Dict) -> None:
        """Initialize current user from JWT payload."""
        self.user_id: str = payload.get("sub", "")
        self.name: str = payload.get("name", "")
        self.tenants: List[Dict] = payload.get("tenants", [])
        self.roles: Dict[str, List[str]] = payload.get("roles", {})
        self.raw_payload: Dict = payload
    
    def has_role(self, service_id: str, role_name: str) -> bool:
        """
        Check if user has a specific role for a service.
        
        Args:
            service_id: The service identifier
            role_name: The role name to check
            
        Returns:
            bool: True if user has the role
        """
        service_roles = self.roles.get(service_id, [])
        return role_name in service_roles
    
    def is_global_admin(self) -> bool:
        """
        Check if user is a global administrator.
        
        Returns:
            bool: True if user has global admin role
        """
        return self.has_role("service-setting-service", "全体管理者")
    
    def is_viewer(self) -> bool:
        """
        Check if user has viewer role.
        
        Returns:
            bool: True if user has viewer role or higher
        """
        return (
            self.is_global_admin() or
            self.has_role("service-setting-service", "閲覧者")
        )


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Verify JWT token and extract user information.
    
    Args:
        credentials: HTTP Authorization credentials from request
        
    Returns:
        CurrentUser: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Fetch public key for verification
        public_key = await get_auth_public_key()
        
        # Decode and verify JWT token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        
        # Create current user from payload
        current_user = CurrentUser(payload)
        
        if not current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        
        return current_user
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def require_global_admin(
    current_user: CurrentUser = Depends(verify_token),
) -> CurrentUser:
    """
    Dependency that requires global admin role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        CurrentUser: The authenticated user
        
    Raises:
        HTTPException: If user doesn't have global admin role
    """
    if not current_user.is_global_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Global administrator role required.",
        )
    return current_user


async def require_viewer(
    current_user: CurrentUser = Depends(verify_token),
) -> CurrentUser:
    """
    Dependency that requires at least viewer role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        CurrentUser: The authenticated user
        
    Raises:
        HTTPException: If user doesn't have viewer role or higher
    """
    if not current_user.is_viewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Viewer role or higher required.",
        )
    return current_user
