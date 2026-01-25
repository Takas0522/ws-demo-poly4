"""TenantServiceAssignment data model."""
from datetime import datetime

from pydantic import BaseModel, Field


class TenantServiceAssignment(BaseModel):
    """
    TenantServiceAssignment model representing service assignment to a tenant.
    
    Attributes:
        id: Record ID (UUID)
        tenantId: Tenant ID
        serviceId: Service ID
        assignedAt: Assignment timestamp
        assignedBy: User ID who performed the assignment
    """
    
    id: str = Field(..., description="Record ID (UUID)")
    tenantId: str = Field(..., description="Tenant ID")
    serviceId: str = Field(..., description="Service ID")
    assignedAt: datetime = Field(..., description="Assignment timestamp")
    assignedBy: str = Field(..., description="User ID who performed the assignment")
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "id": "tsa-001",
                "tenantId": "tenant-002",
                "serviceId": "file-management",
                "assignedAt": "2026-01-15T10:00:00Z",
                "assignedBy": "user-001",
            }
        }
