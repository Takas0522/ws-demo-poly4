from functools import wraps
from typing import Optional, Callable
from fastapi import HTTPException, status, Depends
from app.models.auth import JWTPayload
from app.middleware.auth import get_current_user
from app.core.logger import logger


def require_permission(permission: str, scope: Optional[str] = None) -> Callable:
    """
    Decorator to require specific permission for an endpoint.

    Args:
        permission: Permission string (e.g., "services.create", "services.read")
        scope: Permission scope (e.g., "global", "tenant")
            - "global": User must have global admin role
            - None or "tenant": User must have tenant-level permission

    Example:
        @require_permission("services.create", scope="global")
        async def create_service(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: JWTPayload = Depends(get_current_user), **kwargs):
            # Check if user has required permission
            user_roles = current_user.roles or []

            # For global scope, check if user has global admin role
            if scope == "global":
                if "global-admin" not in user_roles and "system-admin" not in user_roles:
                    logger.warning(
                        f"Permission denied: User {current_user.sub} "
                        f"attempted to access {permission} without global admin role"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Global administrator permission required",
                    )
            else:
                # For tenant scope, check basic permission
                # In a production system, you would check against a permissions table
                # For now, we allow users with admin or manager roles
                if not any(
                    role in user_roles for role in ["admin", "manager", "global-admin", "system-admin"]
                ):
                    logger.warning(
                        f"Permission denied: User {current_user.sub} "
                        f"attempted to access {permission} without sufficient permissions"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission {permission} required",
                    )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
