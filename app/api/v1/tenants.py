"""テナント管理エンドポイント"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from ...schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    TenantUserAddRequest,
    TenantUserResponse
)
from ...services.tenant_service import TenantService
from ...utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=TenantListResponse)
async def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """テナント一覧取得"""
    tenant_service = TenantService()
    tenants = await tenant_service.get_all_tenants(skip=skip, limit=limit)
    
    return TenantListResponse(tenants=tenants, total=len(tenants))


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """テナント詳細取得"""
    tenant_service = TenantService()
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_create: TenantCreate,
    current_user: dict = Depends(require_role(["global_admin", "admin"]))
):
    """テナント作成"""
    tenant_service = TenantService()
    tenant = await tenant_service.create_tenant(tenant_create)
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    current_user: dict = Depends(require_role(["global_admin", "admin"]))
):
    """テナント更新"""
    tenant_service = TenantService()
    
    try:
        tenant = await tenant_service.update_tenant(tenant_id, tenant_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(require_role(["global_admin"]))
):
    """テナント削除"""
    tenant_service = TenantService()
    
    try:
        success = await tenant_service.delete_tenant(tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return None


@router.post("/{tenant_id}/users", status_code=status.HTTP_201_CREATED)
async def add_user_to_tenant(
    tenant_id: str,
    request: TenantUserAddRequest,
    current_user: dict = Depends(require_role(["global_admin", "admin"]))
):
    """テナントにユーザー追加"""
    tenant_service = TenantService()
    
    success = await tenant_service.add_user_to_tenant(
        tenant_id=tenant_id,
        user_id=request.user_id,
        added_by=current_user.get("user_id", "system")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add user to tenant"
        )
    
    return {"message": "User added to tenant successfully"}


@router.get("/{tenant_id}/users", response_model=List[TenantUserResponse])
async def get_tenant_users(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """テナントのユーザー一覧取得"""
    tenant_service = TenantService()
    users = await tenant_service.get_tenant_users(tenant_id)
    
    return [
        TenantUserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            added_at=user.added_at,
            added_by=user.added_by
        )
        for user in users
    ]
