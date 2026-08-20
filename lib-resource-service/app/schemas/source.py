from pydantic import BaseModel, Field, field_serializer
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
    type: str = Field(..., description="资源类型名（component/icon/illus/image/file）")
    name: str = Field(..., description="来源名称")
    is_sync_source: Optional[int] = Field(0, description="是否同步来源（0=否 1=是），默认 0")
    config: Optional[Dict[str, Any]] = Field(None, description="来源配置（JSON）")
    is_active: Optional[int] = Field(1, description="是否启用（1=启用 0=禁用），默认 1")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "手动上传-图标",
                    "type": "icon",
                    "is_sync_source": 0,
                    "is_active": 1
                }
            ]
        }
    }


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="来源名称")
    is_sync_source: Optional[int] = Field(None, description="是否同步来源（0=否 1=是）")
    config: Optional[Dict[str, Any]] = Field(None, description="来源配置（JSON）")
    is_active: Optional[int] = Field(None, description="是否启用（1=启用 0=禁用）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "新名称", "is_active": 1}
            ]
        }
    }