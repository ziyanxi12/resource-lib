from typing import Optional

from pydantic import BaseModel, Field


class SearchAppCreate(BaseModel):
    name: str = Field(..., description="应用名称（必填）")
    remark: Optional[str] = Field(None, description="备注")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "设计助手", "remark": "内部设计搜索工具"}
            ]
        }
    }


class SearchAppUpdate(BaseModel):
    name: Optional[str] = Field(None, description="应用名称")
    remark: Optional[str] = Field(None, description="备注")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "新名称", "remark": "更新备注"}
            ]
        }
    }
