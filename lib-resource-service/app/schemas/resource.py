from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ResourceOut(BaseModel):
    """通用资源响应模型，适用于所有五种类型"""
    id:             int
    resource_type:  int
    resource_type_name: str         # 由路由层填充，如 "component_set"
    name:           str
    unique_key:     str
    file_path:      Optional[str]
    thumbnail_path: Optional[str]
    file_size:      Optional[int]
    mime_type:      Optional[str]
    dimensions:     Optional[dict]
    description:    Optional[str]
    english_name:   Optional[str]
    domain:         Optional[str]
    created_by:     Optional[str]
    sort_order:     int
    created_at:     Optional[datetime]
    updated_at:     Optional[datetime]
    tags:           List[str] = []

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    total: int
    page:  int
    limit: int
    items: List[ResourceOut]


class ResourceUpdateRequest(BaseModel):
    """更新资源元数据，所有字段可选"""
    name:        Optional[str]       = None
    description: Optional[str]       = None
    sort_order:  Optional[int]       = None
    tags:        Optional[List[str]] = None
