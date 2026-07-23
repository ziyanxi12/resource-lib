from pydantic import BaseModel, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime


class ResourceOut(BaseModel):
    id: int
    resource_type: int
    resource_type_name: str
    source_id: int
    name: str
    description: Optional[str] = None
    search_text: Optional[str] = None
    vector_text: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    thumbnail_path: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    group_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_updated_at: Optional[datetime] = None
    vector_updated_at: Optional[datetime] = None
    tags: List[str] = []

    @field_serializer('created_at', 'updated_at', 'data_updated_at', 'vector_updated_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[int]:
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[ResourceOut]


class ResourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    group_id: Optional[int] = None
    search_text: Optional[str] = None
    file_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None