from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID, uuid4


class PricingTier(BaseModel):
    """Pricing tier for a service"""

    plan: str
    price: float
    currency: str = "USD"


class ServiceBase(BaseModel):
    """Base model for services"""

    name: str = Field(..., min_length=1, max_length=255)
    displayName: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    requiredPlan: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    pricing: List[PricingTier] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ServiceCreate(ServiceBase):
    """Model for creating a new service"""

    pass


class ServiceUpdate(BaseModel):
    """Model for updating a service"""

    displayName: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None
    requiredPlan: Optional[List[str]] = None
    features: Optional[List[str]] = None
    pricing: Optional[List[PricingTier]] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceResponse(ServiceBase):
    """Model for service response"""

    id: str
    tenantId: str = "system-internal"
    status: str = "active"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    createdBy: str
    updatedBy: str

    class Config:
        from_attributes = True
        populate_by_name = True


class AssignServiceRequest(BaseModel):
    """Model for assigning service to tenant"""

    serviceId: str = Field(..., min_length=1)


class TenantService(BaseModel):
    """Model for tenant service assignment"""

    serviceId: str
    enabled: bool = True
    enabledAt: datetime = Field(default_factory=datetime.utcnow)
    disabledAt: Optional[datetime] = None


class TenantServiceResponse(BaseModel):
    """Model for tenant service response"""

    success: bool
    tenant: Dict[str, Any]


class ServiceUsageStats(BaseModel):
    """Model for service usage statistics"""

    serviceId: str
    tenantCount: int
    userCount: int = 0


class ServiceAnalytics(BaseModel):
    """Model for service analytics response"""

    totalServices: int
    activeServices: int
    serviceUsage: List[ServiceUsageStats]
