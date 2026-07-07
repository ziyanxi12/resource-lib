from pydantic import BaseModel
from typing import Optional


class ImageUploadResponse(BaseModel):
    id:        int
    name:      str
    file_path: str
    width:     Optional[int]
    height:    Optional[int]
    message:   str
