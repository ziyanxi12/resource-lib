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
from app.services.resource_service import upsert_resource

# Pillow 为可选依赖；无法导入时跳过尺寸提取，不影响上传流程
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
    """
    上传图片：
    1. 生成 UUID 作为图片唯一 ID，保留原始文件扩展名
    2. 保存图片到 FILE_ROOT_DIR/image/{uuid}.{ext}
    3. 用 Pillow 提取宽高（若 Pillow 可用）
    4. 写入 resources 表
    返回写入结果 dict。
    """
    image_id = str(uuid.uuid4())

    # 取扩展名，fallback 为 png
    original_name = file.filename or "image.png"
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "png"

    # 确保目录存在
    image_dir = os.path.join(settings.FILE_ROOT_DIR, "image")
    os.makedirs(image_dir, exist_ok=True)

    file_name     = f"{image_id}.{ext}"
    abs_path      = os.path.join(image_dir, file_name)
    relative_path = f"image/{file_name}"

    # 读取并保存文件
    content = await file.read()
    with open(abs_path, "wb") as f:
        f.write(content)

    file_size = len(content)
    mime_type = file.content_type or f"image/{ext}"

    # 提取图片尺寸（失败不影响上传）
    dimensions = _extract_dimensions(content)

    # 写数据库
    data = {
        "resource_type": int(ResourceType.image),
        "name":          name,
        "unique_key":    image_id,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     mime_type,
        "dimensions":    dimensions,
        "description":   description,
        "created_by":    created_by,
    }
    resource, _ = upsert_resource(db, data)

    return {
        "id":         resource.id,
        "name":       resource.name,
        "file_path":  relative_path,
        "dimensions": dimensions,
        "message":    "图片上传成功",
    }


def _extract_dimensions(content: bytes) -> Optional[dict]:
    """用 Pillow 从字节流中提取图片宽高，Pillow 不可用或解析失败时返回 None。"""
    if not _HAS_PILLOW:
        return None
    try:
        img = PILImage.open(BytesIO(content))
        return {"width": img.width, "height": img.height}
    except Exception:
        return None
