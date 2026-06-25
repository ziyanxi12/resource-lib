from pydantic import BaseModel
from typing import Optional


class TemplateUploadRequest(BaseModel):
    name:        str            # 模版名称（必填）
    description: Optional[str] = None
    hex_data:    str            # 粘贴的 hex 文本（必填）


class TemplateUploadResponse(BaseModel):
    id:        int
    name:      str
    file_path: str
    message:   str
