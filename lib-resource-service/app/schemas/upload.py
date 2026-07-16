from pydantic import BaseModel
from typing import Optional, List


class BatchUploadResponse(BaseModel):
    success: bool
    count: int
    items: List[dict]
    message: str