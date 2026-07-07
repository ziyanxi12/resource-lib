from pydantic import BaseModel
from typing import Optional


class ImageUploadResponse(BaseModel):
    id:        int
    name:      str
    file_path: str
    width:     Optional[float]
    height:    Optional[float]
    message:   str
