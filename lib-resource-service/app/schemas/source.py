from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SourceOut(BaseModel):
    id: int
    code: str
    name: str
    resource_type: int
    is_sync_source: int
    config: Optional[Dict[str, Any]] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceCreate(BaseModel):
    code: str
    name: str
    resource_type: int
    is_sync_source: Optional[int] = 0
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = 1


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    is_sync_source: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = None