from pydantic import BaseModel
from typing import Optional, List


class JWTPayload(BaseModel):
    sub: str
    tenant_id: str
    email: Optional[str] = None
    roles: Optional[List[str]] = None
    iat: Optional[int] = None
    exp: Optional[int] = None
    iss: Optional[str] = None
