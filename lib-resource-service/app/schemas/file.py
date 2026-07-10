from pydantic import BaseModel
from typing import Optional, List


class FileUploadRequest(BaseModel):
    name:        str
    description: Optional[str] = None
    tags:        Optional[List[str]] = None


class FileUploadResponse(BaseModel):
    id:            int
    name:          str
    file_path:     str
    thumbnail_path: str
    message:       str


class BatchUploadResponse(BaseModel):
    success: bool
    count:   int
    items:   List[FileUploadResponse]
    message: str