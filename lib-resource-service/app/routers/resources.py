"""
通用资源路由
GET  /api/resources        列表（支持类型、来源、分组筛选）
GET  /api/resources/{id}   详情
PUT  /api/resources/{id}   更新元数据，同步更新向量库
DELETE /api/resources/{id} 软删除
POST /api/resources/{id}/understand  对资源预览图生成语义描述
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource
from app.services import resource_service, upload_service
from app.schemas.resource import ResourceUpdateRequest
from app.services import vector_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["资源管理"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """返回所有有数据的资源类别及各自的数量"""
    return {"categories": resource_service.get_categories_with_counts(db)}


@router.post("/sync-vectors")
def sync_vectors(
    type: str = Query(..., description="资源类型名，如 component、icon、illus、template、image、file"),
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

    return {
        "total": total,
        "page":  page,
        "limit": limit,
        "items": [_fmt(r) for r in items],
    }


@router.get("/{resource_id}")
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """获取单个资源详情"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    return _fmt(resource)


@router.put("/{resource_id}")
def update_resource(
    resource_id: int,
    body: ResourceUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新资源元数据（名称、描述、标签等）"""
    from datetime import datetime
    
    update_data = body.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)
    
    update_data["data_updated_at"] = datetime.utcnow()

    logger.debug("用户修改数据: resource_id=%d, fields=%s", resource_id, list(update_data.keys()))

    resource = resource_service.update_resource(db, resource_id, update_data)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if tags is not None:
        resource_service.update_tags(db, resource_id, tags)
        resource = resource_service.get_resource_by_id(db, resource_id)
    
    if resource:
        resource.vector_text = resource_service.build_vector_text(resource)
        db.commit()

    logger.debug("数据修改完成: resource_id=%d, data_updated_at=%s", resource_id, resource.data_updated_at)

    return {"message": "更新成功", "id": resource_id}


@router.post("/{resource_id}/understand")
def understand_resource(resource_id: int, db: Session = Depends(get_db)):
    """
    对资源的预览图生成语义描述（图片类型用原图，其他类型用缩略图）。
    同步调用图片理解模块，单张耗时约 10~30 秒；
    定义为 def（非 async）使 FastAPI 将其放入线程池，不阻塞事件循环。
    """
    description = upload_service.understand_image(db, resource_id)
    return {"id": resource_id, "description": description}


@router.delete("/batch")
def batch_delete_resources(
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
        vec_type_map = {
            ResourceType.component: "component",
            ResourceType.template: "template",
            ResourceType.icon: "icon",
            ResourceType.illus: "illustration",
            ResourceType.image: "image",
            ResourceType.file: "file",
        }
        vec_type = vec_type_map.get(ResourceType(resource_type_int))
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.batch_delete(vec_type, [str(i) for i in deleted_ids])
            except Exception as e:
                logger.warning("向量批量删除异常 (type=%s): %s", type, e)

    return {"deleted": count}


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """软删除资源"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    resource_type = resource.resource_type
    rid = resource.id

    ok = resource_service.soft_delete_resource(db, resource_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")

    if settings.VECTOR_SERVICE_ENABLED:
        from app.enums import ResourceType as RT
        vec_type_map = {
            RT.component: "component",
            RT.template: "template",
            RT.icon: "icon",
            RT.illus: "illustration",
            RT.image: "image",
            RT.file: "file",
        }
        vec_type = vec_type_map.get(RT(resource_type))
        if vec_type:
            try:
                from app.clients import vector_client
                vector_client.delete(vec_type, str(rid))
            except Exception as e:
                logger.warning("向量删除异常 (resource_id=%s): %s", rid, e)

    return {"message": "删除成功", "id": resource_id}


def _fmt(r) -> dict:
    return {
        "id": r.id,
        "resource_type": r.resource_type,
        "resource_type_name": ResourceType(r.resource_type).name,
        "source_id": r.source_id,
        "name": r.name,
        "description": r.description,
        "search_text": r.search_text,
        "vector_text": r.vector_text,
        "file_name": r.file_name,
        "file_path": r.file_path,
        "file_size": r.file_size,
        "file_type": r.file_type,
        "width": r.width,
        "height": r.height,
        "thumbnail_path": r.thumbnail_path,
        "raw_data": r.raw_data,
        "group_id": r.group_id,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "data_updated_at": r.data_updated_at.isoformat() if r.data_updated_at else None,
        "vector_updated_at": r.vector_updated_at.isoformat() if r.vector_updated_at else None,
        "tags": [t.tag for t in r.tags],
    }