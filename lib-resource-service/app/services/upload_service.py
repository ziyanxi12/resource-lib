"""
统一批量上传服务
支持所有资源类型的批量上传，统一处理文件存储、数据库入库、向量同步
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import UploadFile

logger = logging.getLogger(__name__)

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
        thumbnails: 缩略图列表（PNG / SVG / JPEG）
        items: 元数据列表
        source_id: 来源ID
        created_by: 创建者
    
    Returns:
        {"success": True, "count": N, "items": [...], "message": "..."}
    """
    file_dir_name = get_file_dir(resource_type)
    file_dir = os.path.join(settings.FILE_ROOT_DIR, file_dir_name)
    
    if resource_type == ResourceType.image:
        thumb_dir = file_dir
        thumb_relative_prefix = file_dir_name
    else:
        thumb_dir = os.path.join(file_dir, "image")
        thumb_relative_prefix = f"{file_dir_name}/image"
    
    os.makedirs(file_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    # ===== 第一阶段：异步保存所有文件 =====
    saved_items = []
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
            thumb_ext = thumbnail.filename.rsplit(".", 1)[-1].lower() if "." in thumbnail.filename else "png"
            thumb_name = f"{file_uuid}_thumb.{thumb_ext}"
            thumb_relative_path = f"{thumb_relative_prefix}/{thumb_name}"
            thumb_abs_path = os.path.join(thumb_dir, thumb_name)
            
            thumb_content = await thumbnail.read()
            with open(thumb_abs_path, "wb") as f:
                f.write(thumb_content)
        else:
            thumb_relative_path = None

        saved_items.append({
            "file_relative_path": file_relative_path,
            "thumb_relative_path": thumb_relative_path,
            "file_size": file_size,
            "file_type": file_type,
            "item": item,
        })

    logger.info("文件保存完成，开始批量入库: type=%s, count=%d", resource_type.name, len(saved_items))

    # ===== 第二阶段：在线程池中批量入库 =====
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        insert_result = await loop.run_in_executor(
            pool,
            _batch_insert_db,
            saved_items,
            int(resource_type),
            source_id,
            created_by,
        )

    resources = insert_result["resources"]
    results = insert_result["results"]

    # ===== 第三阶段：向量同步 =====
    if resources:
        # resources 来自线程池已关闭的 session（detached），需在主 session 重新加载
        resource_ids = [r.id for r in resources]
        from app.models.resource import Resource
        fresh_resources = db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
        vectors_data = [(r, {}) for r in fresh_resources]
        ingest_vectors(resource_type, vectors_data)
        batch_update_vector_time(db, resource_ids)

    logger.info("批量入库完成: count=%d", len(results))

    return {
        "success": True,
        "count": len(results),
        "items": results,
        "message": f"成功上传 {len(results)} 个资源",
    }


def _batch_insert_db(saved_items: List[dict], resource_type: int, source_id: int, created_by: Optional[str]) -> dict:
    """在线程池中执行的同步批量入库（支持分批）"""
    from app.database import SessionLocal
    from app.services.resource_service import batch_create_resources, batch_insert_tags
    
    BATCH_SIZE = 500
    all_resources = []
    all_results = []
    
    for batch_start in range(0, len(saved_items), BATCH_SIZE):
        batch_items = saved_items[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        logger.info("处理第 %d 批: %d 条", batch_num, len(batch_items))
        
        db = SessionLocal()
        try:
            # 构建批量数据
            resources_data = []
            tags_list = []  # 每个资源对应的标签列表（索引与 resources_data 一一对应）
            
            for saved in batch_items:
                item = saved["item"]
                data = {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": item.get("name", ""),
                    "file_name": item.get("file_name"),
                    "file_path": saved["file_relative_path"],
                    "file_size": saved["file_size"],
                    "file_type": saved["file_type"],
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "thumbnail_path": saved["thumb_relative_path"],
                    "description": item.get("description"),
                    "group_id": item.get("group_id"),
                    "search_text": item.get("search_text"),
                    "raw_data": item.get("raw_data") or item.get("meta_json"),
                    "data_updated_at": datetime.utcnow(),
                    "created_by": created_by,
                }
                resources_data.append(data)
                tags_list.append(item.get("tags", []))
            
            # 批量插入资源
            resources = batch_create_resources(db, resources_data)
            
            # 根据 resource_id 批量插入标签
            tags_with_ids = []
            for i, resource in enumerate(resources):
                tags = tags_list[i]
                if tags:
                    tags_with_ids.append((resource.id, tags))
            if tags_with_ids:
                batch_insert_tags(db, tags_with_ids)
            
            # 构建向量文本
            from app.services.resource_service import build_vector_text
            for resource in resources:
                resource.vector_text = build_vector_text(resource)
            db.commit()
            
            all_resources.extend(resources)
            all_results.extend([
                {
                    "id": r.id,
                    "name": r.name,
                    "file_path": r.file_path,
                    "thumbnail_path": r.thumbnail_path,
                }
                for r in resources
            ])
            
            logger.info("第 %d 批入库成功: %d 条", batch_num, len(resources))
            
        except Exception as e:
            logger.error("第 %d 批入库失败: %s", batch_num, str(e))
            raise
        finally:
            db.close()
    
    return {"resources": all_resources, "results": all_results}


def understand_image(db: Session, resource_id: int, prompt: Optional[str] = None) -> str:
    """调用图片语义理解模块，对资源的预览图生成中文语义描述
    
    Args:
        db: 数据库会话
        resource_id: 资源ID
        prompt: 用户提示词（可选），用于引导生成方向
    """
    from app.services.resource_service import get_resource_by_id
    from app.clients import image_understanding
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
        logger.debug("LLM调用入参: resource_id=%d, image_path=%s, prompt=%s", resource_id, abs_path, prompt)
        result = image_understanding.understand_image(abs_path, prompt)
        logger.debug("LLM调用输出: resource_id=%d, result=%s", resource_id, result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM调用失败: resource_id=%d, error=%s", resource_id, str(e))
        raise HTTPException(status_code=502, detail=f"图片语义生成失败: {e}")