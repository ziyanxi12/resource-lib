"""
图片服务
负责：保存上传的图片文件、提取尺寸、写入数据库。
"""

import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import create_resource

try:
    from PIL import Image as PILImage
    from io import BytesIO
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False


async def upload_image(
    db: Session,
    file: UploadFile,
    name: str,
    description: Optional[str] = None,
    created_by: Optional[str] = None,
) -> dict:
    original_name = file.filename or "image.png"
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "png"

    image_dir = os.path.join(settings.FILE_ROOT_DIR, "image")
    os.makedirs(image_dir, exist_ok=True)

    file_name     = f"{uuid.uuid4()}.{ext}"
    relative_path = f"image/{file_name}"
    abs_path      = os.path.join(image_dir, file_name)

    content = await file.read()
    with open(abs_path, "wb") as f:
        f.write(content)

    file_size  = len(content)
    mime_type  = file.content_type or f"image/{ext}"
    dimensions = _extract_dimensions(content)

    data = {
        "resource_type": int(ResourceType.image),
        "name":          name,
        "file_name":     file_name,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     mime_type,
        "dimensions":    dimensions,
        "description":   description,
        "created_by":    created_by,
    }
    resource = create_resource(db, data)

    return {
        "id":         resource.id,
        "name":       resource.name,
        "file_path":  relative_path,
        "dimensions": dimensions,
        "message":    "图片上传成功",
    }


def _extract_dimensions(content: bytes) -> Optional[dict]:
    if not _HAS_PILLOW:
        return None
    try:
        img = PILImage.open(BytesIO(content))
        return {"width": img.width, "height": img.height}
    except Exception:
        return None
