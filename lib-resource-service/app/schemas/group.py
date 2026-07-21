from pydantic import BaseModel
from typing import Optional, List


class GroupNode(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    level: int
    real_path: str
    sort_order: int
    is_default: int = 0
    resource_count: int = 0
    children: List["GroupNode"] = []

    model_config = {"from_attributes": True}


class GroupTreeResponse(BaseModel):
    resource_type: int
    resource_type_name: str
    source_id: Optional[int] = None
    items: List[GroupNode]


class GroupCreate(BaseModel):
    type: str
    source_id: Optional[int] = None
    name: str
    parent_id: Optional[int] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None


class GroupMove(BaseModel):
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class GroupReorderItem(BaseModel):
    id: int
    sort_order: int


class GroupReorderRequest(BaseModel):
    items: List[GroupReorderItem]