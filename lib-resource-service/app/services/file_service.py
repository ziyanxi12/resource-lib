"""
文件服务
负责：保存上传的文件和缩略图、写入数据库、入库向量库。
"""

import os
import uuid
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import create_resource, update_tags
from app.services.vector_text_builder import ingest_vectors


async def upload_file(
    db: Session,
    file: UploadFile,
    thumbnail: UploadFile,
    name: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    created_by: Optional[str] = None,
) -> dict:
    """
    上传文件 + PNG 缩略图
    - 文件保存到 storage/file/{uuid}.{ext}
    - 缩略图保存到 storage/file/{uuid}_thumb.png
    - 入库（resources + resource_tags）
    - 入向量库（name + description + tags）
    """
    file_dir = os.path.join(settings.FILE_ROOT_DIR, "file")
    os.makedirs(file_dir, exist_ok=True)

    file_uuid = str(uuid.uuid4())

    original_name = file.filename or "file"
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"

    file_name = f"{file_uuid}.{ext}"
    relative_path = f"file/{file_name}"
    abs_path = os.path.join(file_dir, file_name)

    content = await file.read()
    with open(abs_path, "wb") as f:
        f.write(content)

    thumb_name = f"{file_uuid}_thumb.png"
    thumb_relative_path = f"file/{thumb_name}"
    thumb_abs_path = os.path.join(file_dir, thumb_name)

    thumb_content = await thumbnail.read()
    with open(thumb_abs_path, "wb") as f:
        f.write(thumb_content)

    file_size = len(content)
    mime_type = file.content_type or "application/octet-stream"

    data = {
        "resource_type": int(ResourceType.file),
        "name": name,
        "file_name": file_name,
        "file_path": relative_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "thumbnail_path": thumb_relative_path,
        "description": description,
        "created_by": created_by,
    }
    resource = create_resource(db, data)

    if tags:
        update_tags(db, resource.id, tags)

    ingest_vectors(
        ResourceType.file,
        [(resource, {"name": name, "description": description or "", "tags": tags or []})]
    )

    return {
        "id": resource.id,
        "name": resource.name,
        "file_path": relative_path,
        "thumbnail_path": thumb_relative_path,
        "message": "文件上传成功",
    }


async def batch_upload_files(
    db: Session,
    files: List[UploadFile],
    thumbnails: List[UploadFile],
    items: List[Dict],
    created_by: Optional[str] = None,
) -> dict:
    """
    批量上传文件 + PNG 缩略图
    - files、thumbnails、items 按索引一一对应
    - 循环调用单文件上传逻辑
    - 批量向量入库
    """
    file_dir = os.path.join(settings.FILE_ROOT_DIR, "file")
    os.makedirs(file_dir, exist_ok=True)

    results = []
    vectors_data = []

    for idx, (file, thumbnail, item) in enumerate(zip(files, thumbnails, items)):
        try:
            file_uuid = str(uuid.uuid4())

            original_name = file.filename or f"file_{idx}"
            ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"

            file_name = f"{file_uuid}.{ext}"
            relative_path = f"file/{file_name}"
            abs_path = os.path.join(file_dir, file_name)

            content = await file.read()
            with open(abs_path, "wb") as f:
                f.write(content)

            thumb_name = f"{file_uuid}_thumb.png"
            thumb_relative_path = f"file/{thumb_name}"
            thumb_abs_path = os.path.join(file_dir, thumb_name)

            thumb_content = await thumbnail.read()
            with open(thumb_abs_path, "wb") as f:
                f.write(thumb_content)

            file_size = len(content)
            mime_type = file.content_type or "application/octet-stream"

            name = item.get("name", "")
            description = item.get("description")
            tags = item.get("tags", [])

            data = {
                "resource_type": int(ResourceType.file),
                "name": name,
                "file_name": file_name,
                "file_path": relative_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "thumbnail_path": thumb_relative_path,
                "description": description,
                "created_by": created_by,
            }
            resource = create_resource(db, data)

            if tags:
                update_tags(db, resource.id, tags)

            vectors_data.append((resource, {
                "name": name,
                "description": description or "",
                "tags": tags or []
            }))

            results.append({
                "id": resource.id,
                "name": resource.name,
                "file_path": relative_path,
                "thumbnail_path": thumb_relative_path,
                "message": "上传成功",
            })

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"第 {idx + 1} 个文件上传失败: {str(e)}"
            )

    if vectors_data:
        ingest_vectors(ResourceType.file, vectors_data)

    return {
        "success": True,
        "count": len(results),
        "items": results,
        "message": f"成功上传 {len(results)} 个文件",
    }