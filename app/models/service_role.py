"""ServiceRole data model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceRole(BaseModel):
    """
    ServiceRole model representing a role within a service.

    This model is used for caching role information from services.

    Attributes:
        id: Record ID (UUID)
        serviceId: Service ID
        roleName: Role name
        description: Role description (optional)
        lastSyncedAt: Last synchronization timestamp (optional)
    """

    id: str = Field(..., description="Record ID (UUID)")
    serviceId: str = Field(..., description="Service ID")
    roleName: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    lastSyncedAt: Optional[datetime] = Field(
        None, description="Last synchronization timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sr-001",
                "serviceId": "file-management",
                "roleName": "ファイル管理者",
                "description": "ファイルの全操作が可能",
                "lastSyncedAt": "2026-01-15T10:00:00Z",
            }
        }
    )
