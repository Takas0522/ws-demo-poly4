"""Service-related schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ServiceResponse(BaseModel):
    """Service response schema."""

    id: str = Field(..., description="Service ID")
    name: str = Field(..., description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    roleEndpoint: str = Field(..., description="Role information endpoint URL")
    isCore: bool = Field(..., description="Core service flag")
    isActive: bool = Field(..., description="Active service flag")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class ServiceListResponse(BaseModel):
    """Service list response schema."""

    data: List[ServiceResponse] = Field(..., description="List of services")


class TenantServiceResponse(BaseModel):
    """Tenant service assignment response schema."""

    serviceId: str = Field(..., description="Service ID")
    serviceName: str = Field(..., description="Service name")
    assignedAt: datetime = Field(..., description="Assignment timestamp")
    assignedBy: str = Field(..., description="User ID who assigned the service")


class TenantServiceListResponse(BaseModel):
    """Tenant service list response schema."""

    data: List[TenantServiceResponse] = Field(
        ..., description="List of services assigned to tenant"
    )


class UpdateTenantServicesRequest(BaseModel):
    """Request schema for updating tenant service assignments."""

    serviceIds: List[str] = Field(
        ..., description="List of service IDs to assign to tenant"
    )


class UpdateTenantServicesResponse(BaseModel):
    """Response schema for updating tenant service assignments."""

    tenantId: str = Field(..., description="Tenant ID")
    assignedServices: List[str] = Field(
        ..., description="List of assigned service IDs"
    )
    message: str = Field(..., description="Success message")
