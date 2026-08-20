from typing import List, Optional

from pydantic import BaseModel, Field


class WhitelistCreate(BaseModel):
    account: str = Field(..., description="登录账号（必填）")
    nick_name: Optional[str] = Field(None, description="昵称（展示用，可留空后补全）")
    remark: Optional[str] = Field(None, description="备注")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"account": "zhangsan", "nick_name": "张三", "remark": "设计部"}
            ]
        }
    }


class WhitelistBatchItem(BaseModel):
    account: str = Field(..., description="登录账号")
    nick_name: Optional[str] = Field(None, description="昵称")
    remark: Optional[str] = Field(None, description="备注")


class WhitelistBatchCreate(BaseModel):
    accounts: List[WhitelistBatchItem] = Field(..., description="账号列表")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accounts": [
                        {"account": "zhangsan", "nick_name": "张三"},
                        {"account": "lisi"}
                    ]
                }
            ]
        }
    }


class WhitelistUpdate(BaseModel):
    nick_name: Optional[str] = Field(None, description="昵称")
    remark: Optional[str] = Field(None, description="备注")
    is_active: Optional[int] = Field(None, description="是否启用（1=启用 0=禁用）")
    role: Optional[str] = Field(None, description="角色（super=超管 admin=管理员）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"nick_name": "新昵称", "is_active": 1}
            ]
        }
    }
