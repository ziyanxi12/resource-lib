"""
通用资源路由
GET  /api/resources        列表（支持类型过滤、搜索、分页）
GET  /api/resources/{id}   详情
PUT  /api/resources/{id}   更新元数据
DELETE /api/resources/{id} 软删除
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ResourceType
from app.services import resource_service
from app.schemas.resource import ResourceUpdateRequest

router = APIRouter(prefix="/api/resources", tags=["资源管理"])


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
    """更新资源元数据（名称、描述、排序等）"""
    update_data = body.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)

    resource = resource_service.update_resource(db, resource_id, update_data)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if tags is not None:
        resource_service.update_tags(db, resource_id, tags)

    return {"message": "更新成功", "id": resource_id}


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """软删除资源"""
    ok = resource_service.soft_delete_resource(db, resource_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")
    return {"message": "删除成功", "id": resource_id}


# ──────────────────────────────────────────────────────────────────
# 辅助
# ──────────────────────────────────────────────────────────────────

def _fmt(r) -> dict:
    """ORM 对象 → 响应字典，附加 resource_type_name 字段"""
    return {
        "id":                 r.id,
        "resource_type":      r.resource_type,
        "resource_type_name": ResourceType(r.resource_type).name,
        "name":               r.name,
        "unique_key":         r.unique_key,
        "file_path":          r.file_path,
        "thumbnail_path":     r.thumbnail_path,
        "file_size":          r.file_size,
        "mime_type":          r.mime_type,
        "dimensions":         r.dimensions,
        "description":        r.description,
        "english_name":       r.english_name,
        "domain":             r.domain,
        "created_by":         r.created_by,
        "sort_order":         r.sort_order,
        "created_at":         r.created_at.isoformat() if r.created_at else None,
        "updated_at":         r.updated_at.isoformat() if r.updated_at else None,
        "tags":               [t.tag for t in r.tags],
    }
