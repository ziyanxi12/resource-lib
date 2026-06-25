from pydantic import BaseModel
from typing import Optional


class ImageUploadResponse(BaseModel):
    id:         int
    name:       str
    file_path:  str
    dimensions: Optional[dict]
    message:    str
