from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID, uuid4


class ConfigurationBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Any
    description: Optional[str] = Field(None, max_length=1000)
    schema_: Optional[str] = Field(None, alias="schema")
    is_encrypted: bool = False
    parent_config_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConfigurationCreate(ConfigurationBase):
    tenant_id: str


class ConfigurationUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = Field(None, max_length=1000)
    schema_: Optional[str] = Field(None, alias="schema")
    is_encrypted: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = Field(None, max_length=500)


class Configuration(ConfigurationBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
        populate_by_name = True


class ConfigurationQuery(BaseModel):
    tenant_id: str
    key: Optional[str] = None
    tags: Optional[List[str]] = None
    include_inherited: bool = False


class ConfigurationVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    config_id: str
    tenant_id: str
    version: int
    value: Any
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_reason: Optional[str] = None


class ConfigurationBackup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    backup_date: datetime = Field(default_factory=datetime.utcnow)
    configurations: List[Configuration]
    created_by: str
    description: Optional[str] = None


class BackupRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=1000)


class BackupResponse(BaseModel):
    backup_id: str


class RestoreResponse(BaseModel):
    message: str
