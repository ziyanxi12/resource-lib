from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ResourceOut(BaseModel):
    id:                 int
    resource_type:      int
    resource_type_name: str
    name:               str
    file_name:          Optional[str]
    file_path:          Optional[str]
    file_size:          Optional[int]
    mime_type:          Optional[str]
    thumbnail_path:     Optional[str]
    dimensions:         Optional[dict]
    description:        Optional[str]
    raw_data:           Optional[str]
    created_by:         Optional[str]
    sort_order:         int
    created_at:         Optional[datetime]
    updated_at:         Optional[datetime]
    tags:               List[str] = []

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    total: int
    page:  int
    limit: int
    items: List[ResourceOut]


class ResourceUpdateRequest(BaseModel):
    name:        Optional[str]       = None
    description: Optional[str]       = None
    sort_order:  Optional[int]       = None
    tags:        Optional[List[str]] = None
