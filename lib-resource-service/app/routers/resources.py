"""
通用资源路由
GET  /api/resources        列表（支持类型过滤、搜索、分页）
GET  /api/resources/{id}   详情
PUT  /api/resources/{id}   更新元数据，同步更新向量库
DELETE /api/resources/{id} 软删除，同步从向量库删除
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource, ComponentVariant, ResourceIcon
from app.services import resource_service
from app.schemas.resource import ResourceUpdateRequest
from app.services.vector_text_builder import build_component_text, build_icon_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["资源管理"])

_VECTOR_TYPES = {
    int(ResourceType.component_set): "component",
    int(ResourceType.svg):           "icon",
}


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """返回所有有数据的资源类别及各自的数量"""
    return {"categories": resource_service.get_categories_with_counts(db)}


@router.get("/all")
def get_all_by_category(
    type_id: int = Query(..., description="资源类型 ID：1=组件集 2=模版 3=SVG 4=插画 5=图片"),
    db: Session = Depends(get_db),
):
    """返回指定类别的全量数据（不分页）"""
    try:
        resource_type = ResourceType(type_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知 type_id: {type_id}，可选值: {[e.value for e in ResourceType]}")

    items, total = resource_service.get_all_by_type(db, type_id)
    return {
        "type_id": type_id,
        "type":    resource_type.name,
        "label":   resource_type.label,
        "total":   total,
        "items":   [_fmt(r) for r in items],
    }


@router.get("")
def list_resources(
    type:   Optional[str] = Query(None, description="资源类型名，如 component_set"),
    page:   int           = Query(1,    ge=1),
    limit:  int           = Query(20,   ge=1, le=100),
    search: Optional[str] = Query(None, description="关键词，匹配名称/英文名/描述"),
    db: Session = Depends(get_db),
):
    """获取资源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    items, total = resource_service.get_resources(db, resource_type_int, search, page, limit)

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
    """更新资源元数据（名称、描述、排序等），组件/图标同步更新向量库"""
    update_data = body.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)

    resource = resource_service.update_resource(db, resource_id, update_data)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if tags is not None:
        resource_service.update_tags(db, resource_id, tags)

    if settings.VECTOR_SERVICE_ENABLED and resource.resource_type in _VECTOR_TYPES:
        _sync_to_vector(db, resource)

    return {"message": "更新成功", "id": resource_id}


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """软删除资源，组件/图标同步从向量库删除"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    resource_type = resource.resource_type
    rid = resource.id

    ok = resource_service.soft_delete_resource(db, resource_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")

    if settings.VECTOR_SERVICE_ENABLED and resource_type in _VECTOR_TYPES:
        vec_type = _VECTOR_TYPES[resource_type]
        try:
            from app.clients import vector_client
            vector_client.delete(vec_type, str(rid))
        except Exception as e:
            logger.warning("向量删除异常 (resource_id=%s): %s", rid, e)

    return {"message": "删除成功", "id": resource_id}


# ──────────────────────────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────────────────────────

def _sync_to_vector(db: Session, resource: Resource) -> None:
    """将单条资源的最新数据同步到向量库（update 接口）。"""
    from app.clients import vector_client

    vec_type = _VECTOR_TYPES[resource.resource_type]

    if resource.resource_type == int(ResourceType.component_set):
        variant = db.query(ComponentVariant).filter(
            ComponentVariant.resource_id == resource.id
        ).first()
        if not variant:
            return
        text = build_component_text(
            variant.component_name or "",
            variant.canvas_name or "",
            variant.name or "",
        )
        metadata = {
            "name":           resource.name,
            "canvas_name":    variant.canvas_name or "",
            "component_name": variant.component_name or "",
            "domain":         variant.domain or "",
        }
    else:
        icon = db.query(ResourceIcon).filter(
            ResourceIcon.resource_id == resource.id
        ).first()
        if not icon:
            return
        text = build_icon_text(
            resource.name,
            icon.english_name or "",
            resource.description or "",
            icon.category or "",
        )
        metadata = {
            "name":         resource.name,
            "description":  resource.description or "",
            "english_name": icon.english_name or "",
            "category":     icon.category or "",
        }

    try:
        vector_client.update(vec_type, str(resource.id), text=text, metadata=metadata)
    except Exception as e:
        logger.warning("向量更新异常 (resource_id=%s): %s", resource.id, e)


def _fmt(r) -> dict:
    return {
        "id":                 r.id,
        "resource_type":      r.resource_type,
        "resource_type_name": ResourceType(r.resource_type).name,
        "name":               r.name,
        "file_name":          r.file_name,
        "file_path":          r.file_path,
        "file_size":          r.file_size,
        "mime_type":          r.mime_type,
        "thumbnail_path":     r.thumbnail_path,
        "dimensions":         r.dimensions,
        "description":        r.description,
        "raw_data":           r.raw_data,
        "created_by":         r.created_by,
        "sort_order":         r.sort_order,
        "created_at":         r.created_at.isoformat() if r.created_at else None,
        "updated_at":         r.updated_at.isoformat() if r.updated_at else None,
        "tags":               [t.tag for t in r.tags],
    }
