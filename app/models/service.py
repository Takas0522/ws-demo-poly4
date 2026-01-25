"""Service data model."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Service(BaseModel):
    """
    Service model representing a service in the system.
    
    Attributes:
        id: Service ID (e.g., file-management)
        name: Service name for display
        description: Service description (optional)
        roleEndpoint: URL endpoint for retrieving role information
        isCore: Core service flag (cannot be deleted if true)
        isActive: Active flag (cannot be assigned if false)
        createdAt: Creation timestamp
        updatedAt: Last update timestamp
    """
    
    id: str = Field(..., description="Service ID (e.g., file-management)")
    name: str = Field(..., description="Service name for display")
    description: Optional[str] = Field(None, description="Service description")
    roleEndpoint: str = Field(
        ..., description="URL endpoint for retrieving role information"
    )
    isCore: bool = Field(
        ..., description="Core service flag (cannot be deleted if true)"
    )
    isActive: bool = Field(
        ..., description="Active flag (cannot be assigned if false)"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "id": "file-management",
                "name": "ファイル管理サービス",
                "description": "ファイルのアップロード、ダウンロード、管理機能を提供",
                "roleEndpoint": "http://mock-services/api/file-management/roles",
                "isCore": False,
                "isActive": True,
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
            }
        }
