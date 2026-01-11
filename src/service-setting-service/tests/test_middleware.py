import pytest
from app.middleware.tenant_isolation import verify_tenant_access
from app.models.auth import JWTPayload
from fastapi import HTTPException


def test_verify_tenant_access_same_tenant():
    """Test tenant access verification with matching tenant"""
    user = JWTPayload(sub="user-123", tenant_id="tenant-123")
    # Should not raise exception
    verify_tenant_access(user, "tenant-123")


def test_verify_tenant_access_different_tenant():
    """Test tenant access verification with different tenant"""
    user = JWTPayload(sub="user-123", tenant_id="tenant-123")
    
    with pytest.raises(HTTPException) as exc_info:
        verify_tenant_access(user, "tenant-456")
    
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


def test_verify_tenant_access_no_tenant():
    """Test tenant access verification with no tenant specified"""
    user = JWTPayload(sub="user-123", tenant_id="tenant-123")
    # Should not raise exception when tenant_id is None
    verify_tenant_access(user, None)
