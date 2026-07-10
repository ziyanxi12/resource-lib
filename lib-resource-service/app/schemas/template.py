from pydantic import BaseModel
from typing import Optional, List


class TemplateUploadRequest(BaseModel):
    name:        str
    description: Optional[str] = None
    hex_data:    str


class TemplateUploadResponse(BaseModel):
    id:        int
    name:      str
    file_path: str
    message:   str


class BatchUploadTemplateItem(BaseModel):
    id:             int
    name:           str
    file_path:      str
    thumbnail_path: str


class BatchUploadTemplateResponse(BaseModel):
    success: bool
    count:   int
    items:   List[BatchUploadTemplateItem]
    message: str = "批量上传成功"
