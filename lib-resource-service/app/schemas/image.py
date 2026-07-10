from pydantic import BaseModel
from typing import Optional, List


class ImageUploadResponse(BaseModel):
    id:        int
    name:      str
    file_path: str
    width:     Optional[float]
    height:    Optional[float]
    message:   str


class BatchUploadItem(BaseModel):
    id:        int
    name:      str
    file_path: str
    width:     Optional[float] = None
    height:    Optional[float] = None


class BatchUploadResponse(BaseModel):
    success: bool
    count:   int
    items:   List[BatchUploadItem]
    message: str = "批量上传成功"
