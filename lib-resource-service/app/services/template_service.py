"""
模版服务
负责：将 hex 文本写入文件，并将元数据写入数据库。
"""

import os
import uuid
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import create_resource, update_tags
from app.services.vector_text_builder import ingest_vectors


ALLOWED_PREVIEW_TYPES = {'png'}
ALLOWED_PREVIEW_MIME_TYPES = {'image/png'}


def upload_template(
    db: Session,
    name: str,
    description: Optional[str],
    hex_data: str,
    created_by: Optional[str] = None,
) -> dict:
    template_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(template_dir, exist_ok=True)

    file_name     = f"{uuid.uuid4()}.txt"
    relative_path = f"template/{file_name}"
    abs_path      = os.path.join(template_dir, file_name)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(hex_data)

    file_size = os.path.getsize(abs_path)

    data = {
        "resource_type": int(ResourceType.template),
        "name":          name,
        "file_name":     file_name,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     "text/plain",
        "description":   description,
        "created_by":    created_by,
    }
    resource = create_resource(db, data)
    ingest_vectors(ResourceType.template, [(resource, {"name": name, "description": description or ""})])

    return {
        "id":        resource.id,
        "name":      resource.name,
        "file_path": relative_path,
        "message":   "模版上传成功",
    }


async def batch_upload_templates(
    db: Session,
    preview_files: List[UploadFile],
    hex_datas: List[str],
    items: List[Dict],
    created_by: Optional[str] = None,
) -> dict:
    """
    批量上传模版
    preview_files: 预览图列表（仅 png）
    hex_datas: hex 文本数据列表
    items: 元数据列表 [{name, description?, tags?}, ...]
    created_by: 上传人
    """
    if len(preview_files) != len(hex_datas) or len(preview_files) != len(items):
        raise HTTPException(
            status_code=400,
            detail=f"预览图数量({len(preview_files)})、hex数据数量({len(hex_datas)})、元数据数量({len(items)})不一致"
        )
    
    image_dir = os.path.join(settings.FILE_ROOT_DIR, "image")
    template_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    
    results = []
    vectors_data = []
    
    for idx, (preview_file, hex_data, item) in enumerate(zip(preview_files, hex_datas, items)):
        try:
            # 校验预览图类型（仅 png）
            preview_ext = preview_file.filename.rsplit(".", 1)[-1].lower() if "." in preview_file.filename else ""
            preview_mime = preview_file.content_type or ""
            
            if preview_ext not in ALLOWED_PREVIEW_TYPES or preview_mime not in ALLOWED_PREVIEW_MIME_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {idx + 1} 个模版预览图仅支持 png 格式"
                )
            
            # 校验名称
            name = item.get("name", "").strip()
            if not name:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {idx + 1} 个模版名称不能为空"
                )
            
            # 校验 hex 数据
            if not hex_data or not hex_data.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {idx + 1} 个模版 hex 数据不能为空"
                )
            
            # 生成唯一标识
            file_uuid = uuid.uuid4()
            
            # 保存预览图
            preview_file_name = f"{file_uuid}.png"
            preview_relative_path = f"image/{preview_file_name}"
            preview_abs_path = os.path.join(image_dir, preview_file_name)
            
            preview_content = await preview_file.read()
            with open(preview_abs_path, "wb") as f:
                f.write(preview_content)
            
            # 保存 hex 文件
            hex_file_name = f"{file_uuid}.txt"
            hex_relative_path = f"template/{hex_file_name}"
            hex_abs_path = os.path.join(template_dir, hex_file_name)
            
            with open(hex_abs_path, "w", encoding="utf-8") as f:
                f.write(hex_data.strip())
            
            hex_file_size = os.path.getsize(hex_abs_path)
            
            # 写入数据库
            data = {
                "resource_type": int(ResourceType.template),
                "name": name,
                "file_name": hex_file_name,
                "file_path": hex_relative_path,
                "thumbnail_path": preview_relative_path,
                "file_size": hex_file_size,
                "mime_type": "text/plain",
                "description": item.get("description"),
                "created_by": created_by,
            }
            
            resource = create_resource(db, data)
            
            # 处理标签
            tags = item.get("tags", [])
            if tags:
                update_tags(db, resource.id, tags)
            
            # 向量库数据
            vectors_data.append((resource, {
                "name": name,
                "description": item.get("description", "") or ""
            }))
            
            results.append({
                "id": resource.id,
                "name": resource.name,
                "file_path": hex_relative_path,
                "thumbnail_path": preview_relative_path,
            })
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"第 {idx + 1} 个模版上传失败: {str(e)}"
            )
    
    # 批量写入向量库
    if vectors_data:
        ingest_vectors(ResourceType.template, vectors_data)
    
    return {
        "success": True,
        "count": len(results),
        "items": results,
        "message": f"成功上传 {len(results)} 个模版",
    }
