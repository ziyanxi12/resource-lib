from pydantic import BaseModel, field_serializer
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

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[int]:
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)

    model_config = {"from_attributes": True}


class SourceCreate(BaseModel):
    type: str
    name: str
    is_sync_source: Optional[int] = 0
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = 1


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    is_sync_source: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = None