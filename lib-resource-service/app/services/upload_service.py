"""
统一批量上传服务
支持所有资源类型的批量上传，统一处理文件存储、数据库入库、向量同步
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import create_resource, update_tags, batch_update_vector_time, build_vector_text
from app.services.vector_text_builder import ingest_vectors


def get_file_dir(resource_type: ResourceType) -> str:
    """根据资源类型返回存储目录名"""
    return {
        ResourceType.component: "component",
        ResourceType.icon: "icon",
        ResourceType.illus: "illus",
        ResourceType.template: "template",
        ResourceType.image: "image",
        ResourceType.file: "file",
    }[resource_type]


def get_mime_type(filename: str) -> str:
    """根据文件扩展名返回 MIME type"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "hex": "text/plain",
    }
    return mime_map.get(ext, "application/octet-stream")


async def batch_upload(
    db: Session,
    resource_type: ResourceType,
    files: List[UploadFile],
    thumbnails: List[UploadFile],
    items: List[Dict],
    source_id: int,
    created_by: Optional[str] = None,
) -> dict:
    """
    统一批量上传
    
    Args:
        db: 数据库会话
        resource_type: 资源类型
        files: 资源文件列表
        thumbnails: 缩略图列表（PNG）
        items: 元数据列表
        source_id: 来源ID
        created_by: 创建者
    
    Returns:
        {"success": True, "count": N, "items": [...], "message": "..."}
    """
    file_dir_name = get_file_dir(resource_type)
    file_dir = os.path.join(settings.FILE_ROOT_DIR, file_dir_name)
    
    # 缩略图目录：image 类型直接放在 image/ 目录，其他类型放在各自目录的 image/ 子目录
    if resource_type == ResourceType.image:
        thumb_dir = file_dir
        thumb_relative_prefix = file_dir_name
    else:
        thumb_dir = os.path.join(file_dir, "image")
        thumb_relative_prefix = f"{file_dir_name}/image"
    
    os.makedirs(file_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    results = []
    vectors_data = []

    for idx, (file, thumbnail, item) in enumerate(zip(files, thumbnails, items)):
        file_uuid = str(uuid.uuid4())

        # 保存资源文件
        if file.filename:
            original_name = file.filename
            ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"
            file_name = f"{file_uuid}.{ext}"
            file_relative_path = f"{file_dir_name}/{file_name}"
            file_abs_path = os.path.join(file_dir, file_name)
            
            content = await file.read()
            with open(file_abs_path, "wb") as f:
                f.write(content)
            
            file_size = len(content)
            file_type = ext
        else:
            file_name = None
            file_relative_path = None
            file_size = None
            file_type = None

        # 保存缩略图
        if thumbnail.filename:
            thumb_name = f"{file_uuid}_thumb.png"
            thumb_relative_path = f"{thumb_relative_prefix}/{thumb_name}"
            thumb_abs_path = os.path.join(thumb_dir, thumb_name)
            
            thumb_content = await thumbnail.read()
            with open(thumb_abs_path, "wb") as f:
                f.write(thumb_content)
        else:
            thumb_relative_path = None

        # 提取元数据
        name = item.get("name", "")
        display_file_name = item.get("file_name")
        description = item.get("description")
        group_id = item.get("group_id")
        tags = item.get("tags", [])
        search_text = item.get("search_text")
        width = item.get("width")
        height = item.get("height")
        raw_data = item.get("raw_data") or item.get("meta_json")

        # 构建资源数据
        data = {
            "resource_type": int(resource_type),
            "source_id": source_id,
            "name": name,
            "file_name": display_file_name,
            "file_path": file_relative_path,
            "file_size": file_size,
            "file_type": file_type,
            "width": width,
            "height": height,
            "thumbnail_path": thumb_relative_path,
            "description": description,
            "group_id": group_id,
            "search_text": search_text,
            "raw_data": raw_data,
            "data_updated_at": datetime.utcnow(),
            "created_by": created_by,
        }

        # 入库
        resource = create_resource(db, data)

        # 处理标签
        if tags:
            update_tags(db, resource.id, tags)
            from app.models.resource import Resource
            resource = db.query(Resource).filter(Resource.id == resource.id).first()

        # 构建向量文本
        resource.vector_text = build_vector_text(resource)
        db.commit()

        vectors_data.append((resource, {}))

        results.append({
            "id": resource.id,
            "name": resource.name,
            "file_path": file_relative_path,
            "thumbnail_path": thumb_relative_path,
        })

    # 批量向量入库
    if vectors_data:
        ingest_vectors(resource_type, vectors_data)
        resource_ids = [r.id for r, _ in vectors_data]
        batch_update_vector_time(db, resource_ids)

    return {
        "success": True,
        "count": len(results),
        "items": results,
        "message": f"成功上传 {len(results)} 个资源",
    }


def understand_image(db: Session, resource_id: int, prompt: Optional[str] = None) -> str:
    """调用图片语义理解模块，对资源的预览图生成中文语义描述
    
    Args:
        db: 数据库会话
        resource_id: 资源ID
        prompt: 用户提示词（可选），用于引导生成方向
    """
    from app.services.resource_service import get_resource_by_id
    from app.clients import external
    from fastapi import HTTPException

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
        return external.understand_image(abs_path, prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"图片语义生成失败: {e}")