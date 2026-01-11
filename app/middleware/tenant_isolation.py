from fastapi import HTTPException, status
from app.core.logger import logger
from app.models.auth import JWTPayload
from typing import Optional


def verify_tenant_access(user: JWTPayload, tenant_id: Optional[str]) -> None:
    """Verify user has access to the requested tenant"""
    if tenant_id and tenant_id != user.tenant_id:
        logger.warning(
            f"Tenant isolation violation: User {user.sub} attempted to access tenant {tenant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to different tenant"
        )
