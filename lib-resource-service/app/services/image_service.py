"""
图片服务
负责：保存上传的图片文件、提取尺寸、写入数据库。
"""

import os
import uuid
import json
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.services.resource_service import create_resource, get_resource_by_id, update_tags
from app.services.vector_text_builder import ingest_vectors

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

    file_size     = len(content)
    mime_type     = file.content_type or f"image/{ext}"
    width, height = _extract_dimensions(content)

    data = {
        "resource_type": int(ResourceType.image),
        "name":          name,
        "file_name":     file_name,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     mime_type,
        "width":         width,
        "height":        height,
        "description":   description,
        "created_by":    created_by,
    }
    resource = create_resource(db, data)
    ingest_vectors(ResourceType.image, [(resource, {"name": name, "description": description or ""})])

    return {
        "id":        resource.id,
        "name":      resource.name,
        "file_path": relative_path,
        "width":     width,
        "height":    height,
        "message":   "图片上传成功",
    }


def understand_image(db: Session, resource_id: int) -> str:
    """调用图片语义理解模块，对资源的预览图生成中文语义描述。
    图片类型优先用原图（file_path），其他类型用预览图（thumbnail_path）。
    """
    resource = get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if resource.resource_type == int(ResourceType.image):
        rel_path = resource.file_path or resource.thumbnail_path
    else:
        rel_path = resource.thumbnail_path
    if not rel_path:
        raise HTTPException(status_code=400, detail="该资源没有可用的预览图")

    abs_path = os.path.abspath(os.path.join(settings.FILE_ROOT_DIR, rel_path))
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail=f"预览图文件不存在: {rel_path}")

    try:
        return external.understand_image(abs_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"图片语义生成失败: {e}")


def _extract_dimensions(content: bytes) -> Tuple[Optional[int], Optional[int]]:
    if not _HAS_PILLOW:
        return None, None
    try:
        img = PILImage.open(BytesIO(content))
        return img.width, img.height
    except Exception:
        return None, None


ALLOWED_EXTENSIONS = {'png', 'svg', 'jpeg', 'jpg', 'webp'}
ALLOWED_MIME_TYPES = {'image/png', 'image/svg+xml', 'image/jpeg', 'image/webp'}


async def batch_upload_images(
    db: Session,
    files: List[UploadFile],
    items: List[Dict],
    created_by: Optional[str] = None,
) -> dict:
    """
    批量上传图片
    files: 图片文件列表
    items: 元数据列表 [{name, description?, tags?}, ...]
    created_by: 上传人
    """
    if len(files) != len(items):
        raise HTTPException(
            status_code=400,
            detail=f"文件数量({len(files)})与元数据数量({len(items)})不一致"
        )
    
    image_dir = os.path.join(settings.FILE_ROOT_DIR, "image")
    os.makedirs(image_dir, exist_ok=True)
    
    results = []
    vectors_data = []
    
    for idx, (file, item) in enumerate(zip(files, items)):
        try:
            original_name = file.filename or f"image_{idx}.png"
            ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
            mime_type = file.content_type or ""
            
            if ext not in ALLOWED_EXTENSIONS or mime_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {idx + 1} 张图片类型不支持：仅允许 png/svg/jpeg/webp"
                )
            
            file_name = f"{uuid.uuid4()}.{ext}"
            relative_path = f"image/{file_name}"
            abs_path = os.path.join(image_dir, file_name)
            
            content = await file.read()
            with open(abs_path, "wb") as f:
                f.write(content)
            
            file_size = len(content)
            mime_type = file.content_type or f"image/{ext}"
            width, height = _extract_dimensions(content)
            
            data = {
                "resource_type": int(ResourceType.image),
                "name": item.get("name", ""),
                "file_name": file_name,
                "file_path": relative_path,
                "thumbnail_path": relative_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "width": width,
                "height": height,
                "description": item.get("description"),
                "created_by": created_by,
            }
            
            resource = create_resource(db, data)
            
            tags = item.get("tags", [])
            if tags:
                update_tags(db, resource.id, tags)
            
            vectors_data.append((resource, {
                "name": item.get("name", ""),
                "description": item.get("description", "") or ""
            }))
            
            results.append({
                "id": resource.id,
                "name": resource.name,
                "file_path": relative_path,
                "width": width,
                "height": height,
            })
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"第 {idx + 1} 张图片上传失败: {str(e)}"
            )
    
    if vectors_data:
        ingest_vectors(ResourceType.image, vectors_data)
    
    return {
        "success": True,
        "count": len(results),
        "items": results,
        "message": f"成功上传 {len(results)} 张图片",
    }
