"""
通用资源路由
GET  /api/resources        列表（支持类型、来源、分组筛选）
GET  /api/resources/{id}   详情
PUT  /api/resources/{id}   更新元数据，同步更新向量库
DELETE /api/resources/{id} 软删除
POST /api/resources/{id}/understand  对资源预览图生成语义描述
"""

import logging
import re
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource
from app.services import resource_service, upload_service
from app.services import vector_sync_service
from app.services import image_meta_service
from app.services import operation_log_service
from app.services.operator import get_operator
from app.services.user_service import resolve_display_names

logger = logging.getLogger(__name__)

class UnderstandRequest(BaseModel):
    prompt: Optional[str] = None
    image_base64: Optional[str] = None

class BatchIdsRequest(BaseModel):
    ids: List[int]
    type: str

class BatchMoveRequest(BaseModel):
    ids: List[int]
    group_id: int
    type: str

router = APIRouter(prefix="/api/resources", tags=["资源管理"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """返回所有有数据的资源类别及各自的数量"""
    return {"categories": resource_service.get_categories_with_counts(db)}


@router.get("/tags")
def get_tags(
    type: Optional[str] = Query(None, description="资源类型名"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    db: Session = Depends(get_db),
):
    """获取去重标签列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    items = resource_service.get_all_tags(db, resource_type=resource_type_int, source_id=source_id)
    return {"items": items}


@router.post("/sync-vectors")
def sync_vectors(
    request: Request,
    type: str = Query(..., description="资源类型名，如 component、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    db: Session = Depends(get_db),
):
    """
    批量同步指定类型的向量数据。
    仅同步 vector_updated_at < data_updated_at 的数据。
    """
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    
    result = vector_sync_service.sync_vectors_by_type(db, resource_type, source_id)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=source_id,
        resource_type=int(resource_type),
        operator=name,
        operator_account=account,
        action="vector_sync",
        target_type="resource",
        detail={"type": type, "synced": result.get("synced"), "skipped": result.get("skipped")},
    )

    return result


@router.get("")
def list_resources(
    type:       Optional[str] = Query(None, description="资源类型名，如 component、icon、illus"),
    source_id:  Optional[int] = Query(None, description="来源ID筛选"),
    group_id:   Optional[int] = Query(None, description="分组ID筛选"),
    page:       int           = Query(1, ge=1),
    limit:      int           = Query(20, ge=1, le=100),
    search:     Optional[str] = Query(None, description="关键词，匹配名称/描述/search_text"),
    db: Session = Depends(get_db),
):
    """获取资源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    items, total = resource_service.get_resources(
        db,
        resource_type=resource_type_int,
        source_id=source_id,
        search=search,
        page=page,
        limit=limit,
        group_id=group_id,
    )

    accounts = set()
    for r in items:
        if r.created_by: accounts.add(r.created_by)
        if r.updated_by: accounts.add(r.updated_by)
    display_map = resolve_display_names(db, list(accounts))

    return {
        "total": total,
        "page":  page,
        "limit": limit,
        "items": [_fmt(r, display_map) for r in items],
    }


@router.get("/{resource_id}")
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """获取单个资源详情"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    _ensure_dimensions(db, resource)
    display_map = resolve_display_names(db, [x for x in [resource.created_by, resource.updated_by] if x])
    return _fmt(resource, display_map)


def _ensure_dimensions(db: Session, resource: Resource) -> None:
    """若 width/height 缺失，从缩略图读取并回写数据库（读一次即持久化）。"""
    if resource.width is not None and resource.height is not None:
        return
    if not resource.thumbnail_path:
        return
    dims = image_meta_service.read_thumbnail_dimensions(resource.thumbnail_path)
    if dims is None:
        return
    resource.width, resource.height = dims
    try:
        db.commit()
        db.refresh(resource)
        logger.info("回填宽高: resource_id=%s, width=%s, height=%s", resource.id, resource.width, resource.height)
    except Exception as e:
        db.rollback()
        logger.error("回填宽高失败: resource_id=%s, error=%s", resource.id, e)


@router.put("/batch-move")
def batch_move_to_group(
    req: BatchMoveRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """批量移动资源到指定分组，并同步向量库 metadata"""
    try:
        resource_type = ResourceType.from_name(req.type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {req.type}")

    moved_ids, count = resource_service.batch_move_group(db, req.ids, req.group_id)

    if settings.VECTOR_SERVICE_ENABLED and moved_ids:
        vec_type = resource_type.vec_type
        if vec_type:
            try:
                from app.models.resource import Resource as ResModel
                resources = (
                    db.query(ResModel)
                    .filter(ResModel.id.in_(moved_ids))
                    .all()
                )
                from app.clients import vector_client
                for res in resources:
                    vector_client.update(vec_type, str(res.id), metadata={
                        "source_id": res.source_id,
                        "group_id": res.group_id,
                        "tags": res.tags or [],
                    })
            except Exception as e:
                logger.warning("向量 metadata 更新异常 (批量移动 type=%s): %s", req.type, e)

    account, name = get_operator(request)
    source_id_val = None
    if moved_ids:
        from app.models.resource import Resource as ResModel
        res = db.query(ResModel).filter(ResModel.id == moved_ids[0]).first()
        if res:
            source_id_val = res.source_id
    operation_log_service.create_log(
        db,
        source_id=source_id_val,
        resource_type=int(resource_type),
        operator=name,
        operator_account=account,
        action="batch_move",
        target_type="resource",
        detail={"count": count, "target_group_id": req.group_id, "ids": moved_ids},
    )

    return {"moved": count}


@router.put("/{resource_id}")
async def update_resource(
    resource_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    group_id: Optional[int] = Form(None),
    search_text: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None),
    raw_data: Optional[str] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
):
    """更新资源元数据（名称、描述、标签等）及文件"""
    import json
    import os
    import uuid
    from datetime import datetime
    from app.config import settings
    from app.enums import ResourceType
    
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if search_text is not None:
        update_data["search_text"] = search_text
    if file_name is not None:
        update_data["file_name"] = file_name
    if raw_data is not None:
        try:
            update_data["raw_data"] = json.loads(raw_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="raw_data JSON 格式错误")
    if group_id is not None:
        update_data["group_id"] = group_id
    
    tags_list = None
    if tags is not None:
        try:
            tags_list = json.loads(tags)
        except:
            tags_list = None
    
    if thumbnail:
        ext = thumbnail.filename.rsplit(".", 1)[-1].lower() if "." in thumbnail.filename else "png"
        thumb_uuid = str(uuid.uuid4())
        thumb_name = f"{thumb_uuid}_thumb.{ext}"
        
        resource_type = ResourceType(resource.resource_type)
        if resource_type == ResourceType.image:
            thumb_dir = os.path.join(settings.FILE_ROOT_DIR, "image")
            thumb_relative_path = f"image/{thumb_name}"
        else:
            type_dir_map = {
                ResourceType.component: "component",
                ResourceType.icon: "icon",
                ResourceType.illus: "illus",
                    ResourceType.file: "file",
            }
            type_dir = type_dir_map.get(resource_type, "file")
            thumb_dir = os.path.join(settings.FILE_ROOT_DIR, type_dir, "image")
            thumb_relative_path = f"{type_dir}/image/{thumb_name}"
        
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_abs_path = os.path.join(thumb_dir, thumb_name)
        
        content = await thumbnail.read()
        with open(thumb_abs_path, "wb") as f:
            f.write(content)
        
        update_data["thumbnail_path"] = thumb_relative_path
        logger.info("更新缩略图: resource_id=%d, path=%s", resource_id, thumb_relative_path)
    
    if file:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
        file_uuid = str(uuid.uuid4())
        file_name_new = f"{file_uuid}.{ext}"
        
        resource_type = ResourceType(resource.resource_type)
        type_dir_map = {
            ResourceType.component: "component",
            ResourceType.icon: "icon",
            ResourceType.illus: "illus",
            ResourceType.image: "image",
            ResourceType.file: "file",
        }
        type_dir = type_dir_map.get(resource_type, "file")
        file_dir = os.path.join(settings.FILE_ROOT_DIR, type_dir)
        file_relative_path = f"{type_dir}/{file_name_new}"
        
        os.makedirs(file_dir, exist_ok=True)
        file_abs_path = os.path.join(file_dir, file_name_new)
        
        content = await file.read()
        with open(file_abs_path, "wb") as f:
            f.write(content)
        
        update_data["file_path"] = file_relative_path
        update_data["file_type"] = ext
        update_data["file_size"] = len(content)
        logger.info("更新文件: resource_id=%d, path=%s, size=%d", resource_id, file_relative_path, len(content))
    
    text_fields = {"name", "description", "search_text", "raw_data"}
    text_changed = any(k in update_data for k in text_fields)
    group_id_changed = "group_id" in update_data

    if update_data:
        if text_changed:
            update_data["data_updated_at"] = datetime.now()
        logger.debug("用户修改数据: resource_id=%d, fields=%s", resource_id, list(update_data.keys()))
        
        for key, value in update_data.items():
            setattr(resource, key, value)
        db.commit()
        db.refresh(resource)
    
    if tags_list is not None:
        resource.tags = resource_service.normalize_tags(tags_list)
        text_changed = True
        if not (update_data and "data_updated_at" in update_data):
            resource.data_updated_at = datetime.now()
        db.commit()
        db.refresh(resource)
    
    if resource:
        resource.vector_text = resource_service.build_vector_text(resource)
        db.commit()

    if group_id_changed and not text_changed and settings.VECTOR_SERVICE_ENABLED:
        vec_type = ResourceType(resource.resource_type).vec_type
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.update(vec_type, str(resource.id), metadata={
                    "source_id": resource.source_id,
                    "group_id": resource.group_id,
                    "tags": resource.tags or [],
                })
            except Exception as e:
                logger.warning("向量 metadata 更新异常 (resource_id=%d): %s", resource_id, e)

    logger.debug("数据修改完成: resource_id=%d, data_updated_at=%s", resource_id, resource.data_updated_at)

    account, name = get_operator(request)
    resource.updated_by = account
    db.commit()

    operation_log_service.create_log(
        db,
        source_id=resource.source_id,
        resource_type=resource.resource_type,
        operator=name,
        operator_account=account,
        action="update",
        target_type="resource",
        target_id=resource.id,
        target_name=resource.name,
        detail={"fields": list(update_data.keys()) + (["tags"] if tags_list is not None else [])},
    )

    return {"message": "更新成功", "id": resource_id}


@router.post("/{resource_id}/understand")
def understand_resource(
    resource_id: int,
    request: Request,
    db: Session = Depends(get_db),
    request_body: Optional[UnderstandRequest] = None,
):
    """
    对资源的预览图生成语义描述（图片类型用原图，其他类型用缩略图）。
    同步调用图片理解模块，单张耗时约 10~30 秒；
    定义为 def（非 async）使 FastAPI 将其放入线程池，不阻塞事件循环。
    
    Args:
        resource_id: 资源ID
        request: 请求体，包含 prompt（可选，引导生成方向）和 image_base64
                 （可选，前端构造的图片 base64，不含 data: 前缀；为空时后端从磁盘读取兜底）
    """
    prompt = request_body.prompt if request_body else None
    image_base64 = request_body.image_base64 if request_body else None
    description = upload_service.understand_image(db, resource_id, prompt, image_base64=image_base64)

    account, name = get_operator(request)
    resource = resource_service.get_resource_by_id(db, resource_id)
    operation_log_service.create_log(
        db,
        source_id=resource.source_id if resource else None,
        resource_type=resource.resource_type if resource else None,
        operator=name,
        operator_account=account,
        action="ai_understand",
        target_type="resource",
        target_id=resource_id,
        target_name=resource.name if resource else None,
        detail={"prompt": prompt},
    )

    return {"id": resource_id, "description": description}


@router.delete("/batch")
def batch_delete_resources(
    request: Request,
    type: str = Query(..., description="资源类型名"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    group_id: Optional[int] = Query(None, description="分组ID筛选"),
    db: Session = Depends(get_db),
):
    """批量删除指定类型+来源+分组的所有资源（软删除）"""
    try:
        resource_type_int = int(ResourceType.from_name(type))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    deleted_ids, count = resource_service.batch_soft_delete_by_filters(
        db,
        resource_type=resource_type_int,
        source_id=source_id,
        group_id=group_id,
    )

    if settings.VECTOR_SERVICE_ENABLED and deleted_ids:
        vec_type = ResourceType(resource_type_int).vec_type
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.batch_delete(vec_type, [str(i) for i in deleted_ids])
            except Exception as e:
                logger.warning("向量批量删除异常 (type=%s): %s", type, e)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=source_id,
        resource_type=resource_type_int,
        operator=name,
        operator_account=account,
        action="batch_clear" if group_id else "batch_delete",
        target_type="resource",
        detail={"count": count, "filters": {"type": type, "source_id": source_id, "group_id": group_id}},
    )

    return {"deleted": count}


@router.delete("/batch-ids")
def batch_delete_by_ids(
    req: BatchIdsRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """按 ID 列表批量软删除资源"""
    try:
        resource_type_int = int(ResourceType.from_name(req.type))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {req.type}")

    deleted_ids, count = resource_service.batch_soft_delete_by_ids(db, req.ids)

    if settings.VECTOR_SERVICE_ENABLED and deleted_ids:
        vec_type = ResourceType(resource_type_int).vec_type
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.batch_delete(vec_type, [str(i) for i in deleted_ids])
            except Exception as e:
                logger.warning("向量批量删除异常 (type=%s): %s", req.type, e)

    account, name = get_operator(request)
    source_id_val = None
    if deleted_ids:
        from app.models.resource import Resource as ResModel
        res = db.query(ResModel).filter(ResModel.id == deleted_ids[0]).first()
        if res:
            source_id_val = res.source_id
    operation_log_service.create_log(
        db,
        source_id=source_id_val,
        resource_type=resource_type_int,
        operator=name,
        operator_account=account,
        action="batch_delete",
        target_type="resource",
        detail={"count": count, "ids": req.ids},
    )

    return {"deleted": count}


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, request: Request, db: Session = Depends(get_db)):
    """软删除资源"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    resource_type = resource.resource_type
    rid = resource.id
    r_name = resource.name
    r_source_id = resource.source_id

    ok = resource_service.soft_delete_resource(db, resource_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")

    if settings.VECTOR_SERVICE_ENABLED:
        vec_type = ResourceType(resource_type).vec_type
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.delete(vec_type, str(rid))
            except Exception as e:
                logger.warning("向量删除异常 (resource_id=%s): %s", rid, e)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=r_source_id,
        resource_type=resource_type,
        operator=name,
        operator_account=account,
        action="delete",
        target_type="resource",
        target_id=rid,
        target_name=r_name,
    )

    return {"message": "删除成功", "id": resource_id}


def _to_public_url(path: Optional[str]) -> Optional[str]:
    """将相对路径转为可外部访问的完整 URL；已是完整 URL 则原样返回。"""
    if not path:
        return None
    if re.match(r"^(https?:)?//", path, re.I):
        return path
    if settings.PUBLIC_ORIGIN:
        return f"{settings.PUBLIC_ORIGIN.rstrip('/')}{settings.ROOT_PATH}/static/{path}"
    return f"{settings.ROOT_PATH}/static/{path}"


def _fmt(r, display_map=None) -> dict:
    def _display(val):
        if not val:
            return val
        if display_map:
            return display_map.get(val, val)
        return val
    return {
        "id": r.id,
        "resource_type": r.resource_type,
        "resource_type_name": ResourceType(r.resource_type).name,
        "source_id": r.source_id,
        "name": r.name,
        "description": r.description,
        "ai_description": r.ai_description,
        "search_text": r.search_text,
        "vector_text": r.vector_text,
        "file_name": r.file_name,
        "file_path": _to_public_url(r.file_path),
        "file_size": r.file_size,
        "file_type": r.file_type,
        "width": r.width,
        "height": r.height,
        "thumbnail_path": _to_public_url(r.thumbnail_path),
        "raw_data": r.raw_data,
        "group_id": r.group_id,
        "group_path": r.group.real_path if r.group else None,
        "created_by": _display(r.created_by),
        "updated_by": _display(r.updated_by),
        "created_at": int(r.created_at.timestamp() * 1000) if r.created_at else None,
        "updated_at": int(r.updated_at.timestamp() * 1000) if r.updated_at else None,
        "data_updated_at": int(r.data_updated_at.timestamp() * 1000) if r.data_updated_at else None,
        "vector_updated_at": int(r.vector_updated_at.timestamp() * 1000) if r.vector_updated_at else None,
        "tags": r.tags or [],
    }