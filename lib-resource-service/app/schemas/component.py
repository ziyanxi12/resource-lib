from pydantic import BaseModel
from typing import List


class ComponentMapItem(BaseModel):
    """component_map.json 中的单条记录"""
    fileKey: str
    name:    str


class ComponentSyncRequest(BaseModel):
    file_key: str  # 对应 component_map.json 中的 fileKey


class ComponentSyncResponse(BaseModel):
    file_key: str
    added:    int
    updated:  int
    message:  str
