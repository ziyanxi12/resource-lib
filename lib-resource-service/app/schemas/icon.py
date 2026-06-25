from pydantic import BaseModel
from typing import Literal


class IconSyncRequest(BaseModel):
    # svg 或 illustration，决定写入 resource_type 字段的值
    type: Literal["svg", "illustration"]


class IconSyncResponse(BaseModel):
    type:    str
    added:   int
    updated: int
    message: str
