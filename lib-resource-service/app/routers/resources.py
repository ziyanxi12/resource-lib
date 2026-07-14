"""
通用资源路由
GET  /api/resources        列表（支持类型过滤、搜索、分页）
GET  /api/resources/{id}   详情
PUT  /api/resources/{id}   更新元数据，同步更新向量库
DELETE /api/resources/{id} 软删除，同步从向量库删除
POST /api/resources/{id}/understand  对资源预览图生成语义描述
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource
from app.services import resource_service, image_service
from app.schemas.resource import ResourceUpdateRequest
from app.services.vector_text_builder import get_registry, ingest_vectors
from app.services import vector_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["资源管理"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """返回所有有数据的资源类别及各自的数量"""
    return {"categories": resource_service.get_categories_with_counts(db)}


@router.get("/all")
def get_all_by_category(
    type_id: int = Query(..., description="资源类型 ID：1=component 2=template 3=icon 4=illus 5=image"),
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


@router.get("/filter-options")
def get_filter_options(
    type: str = Query(..., description="资源类型名，如 component、icon、illus"),
    db: Session = Depends(get_db),
):
    """返回指定类型各可筛选字段的去重取值，供前端表头筛选项使用"""
    try:
        resource_type_int = int(ResourceType.from_name(type))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    return {"options": resource_service.get_filter_options(db, resource_type_int)}


@router.post("/sync-vectors")
def sync_vectors(
    type: str = Query(..., description="资源类型名，如 component、icon、illus、template、image、file"),
    db: Session = Depends(get_db),
):
    """
    批量同步指定类型的向量数据。
    仅同步 vector_updated_at < updated_at 的数据。
    """
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    
    result = vector_sync_service.sync_vectors_by_type(db, resource_type)
    return result


@router.get("")
def list_resources(
    type:   Optional[str] = Query(None, description="资源类型名，如 component、icon、illus"),
    page:   int           = Query(1,    ge=1),
    limit:  int           = Query(20,   ge=1, le=100),
    search: Optional[str] = Query(None, description="关键词，匹配名称/英文名/描述"),
    group_id:          Optional[int]    = Query(None, description="分组ID筛选"),
    cv_lib_name:       Optional[List[str]] = Query(None, description="组件-组件库"),
    cv_canvas_name:    Optional[List[str]] = Query(None, description="组件-类别"),
    cv_component_name: Optional[List[str]] = Query(None, description="组件-组件名"),
    icon_category:     Optional[List[str]] = Query(None, description="图标-分类"),
    icon_group:        Optional[List[str]] = Query(None, description="图标-领域"),
    illus_category:    Optional[List[str]] = Query(None, description="插画-分类"),
    illus_version:     Optional[List[str]] = Query(None, description="插画-版本"),
    illus_theme:       Optional[List[str]] = Query(None, description="插画-主题"),
    db: Session = Depends(get_db),
):
    """获取资源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    filters = {
        k: v for k, v in {
            "cv_lib_name": cv_lib_name,
            "cv_canvas_name": cv_canvas_name,
            "cv_component_name": cv_component_name,
            "icon_category": icon_category,
            "icon_group": icon_group,
            "illus_category": illus_category,
            "illus_version": illus_version,
            "illus_theme": illus_theme,
        }.items() if v
    }

    items, total = resource_service.get_resources(db, resource_type_int, search, page, limit, filters, group_id)

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
    """更新资源元数据（名称、描述、排序等），仅更新数据库，不触发向量同步"""
    from datetime import datetime
    from app.models.resource import ResourceIcon
    
    update_data = body.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)
    
    update_data["data_updated_at"] = datetime.utcnow()

    logger.debug("用户修改数据: resource_id=%d, fields=%s", resource_id, list(update_data.keys()))
    logger.debug("修改详情: %s", update_data)
    if tags is not None:
        logger.debug("修改标签: resource_id=%d, tags=%s", resource_id, tags)

    resource = resource_service.update_resource(db, resource_id, update_data)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    # 同步更新 icon 表的 name 字段
    if "name" in update_data and resource.resource_type == ResourceType.icon:
        icon_detail = db.query(ResourceIcon).filter(ResourceIcon.resource_id == resource_id).first()
        if icon_detail:
            icon_detail.name = update_data["name"]
            logger.debug("同步更新 icon.name: resource_id=%d, name=%s", resource_id, update_data["name"])

    if tags is not None:
        resource_service.update_tags(db, resource_id, tags)

    logger.debug("数据修改完成: resource_id=%d, data_updated_at=%s", resource_id, resource.data_updated_at)

    return {"message": "更新成功", "id": resource_id}


@router.post("/{resource_id}/understand")
def understand_resource(resource_id: int, db: Session = Depends(get_db)):
    """
    对资源的预览图生成语义描述（图片类型用原图，其他类型用缩略图）。
    同步调用图片理解模块，单张耗时约 10~30 秒；
    定义为 def（非 async）使 FastAPI 将其放入线程池，不阻塞事件循环。
    """
    description = image_service.understand_image(db, resource_id)
    return {"id": resource_id, "description": description}


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """软删除资源，同步从向量库删除"""
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    resource_type = resource.resource_type
    rid = resource.id

    ok = resource_service.soft_delete_resource(db, resource_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")

    if settings.VECTOR_SERVICE_ENABLED:
        spec = get_registry().get(ResourceType(resource_type))
        if spec:
            try:
                from app.clients import vector_client
                vector_client.delete(spec.vec_type, str(rid))
            except Exception as e:
                logger.warning("向量删除异常 (resource_id=%s): %s", rid, e)

    return {"message": "删除成功", "id": resource_id}


# ──────────────────────────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────────────────────────

def _sync_to_vector(db: Session, resource: Resource) -> None:
    """将单条资源的最新数据同步到向量库（update 接口）。"""
    spec = get_registry().get(ResourceType(resource.resource_type))
    if spec is None:
        return
    try:
        text     = spec.build_text(resource, {})
        metadata = spec.build_metadata(resource, {})
        from app.clients import vector_client
        vector_client.update(spec.vec_type, str(resource.id), text=text, metadata=metadata)
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
        "width":              r.width,
        "height":             r.height,
        "description":        r.description,
        "raw_data":           r.raw_data,
        "group_id":           r.group_id,
        "created_by":         r.created_by,
        "created_at":         r.created_at.isoformat() if r.created_at else None,
        "updated_at":         r.updated_at.isoformat() if r.updated_at else None,
        "data_updated_at":    r.data_updated_at.isoformat() if r.data_updated_at else None,
        "vector_updated_at":  r.vector_updated_at.isoformat() if r.vector_updated_at else None,
        "tags":               [t.tag for t in r.tags],
        "vector_text":        _build_vector_text(r),
        # icon 字段
        "icon_id":            r.icon_detail.icon_id      if r.icon_detail else None,
        "icon_chinese_name":  r.icon_detail.chinese_name if r.icon_detail else None,
        "icon_name":          r.icon_detail.name         if r.icon_detail else None,
        "icon_english_name":  r.icon_detail.english_name if r.icon_detail else None,
        "icon_category":      r.icon_detail.category     if r.icon_detail else None,
        "icon_group":         r.icon_detail.group        if r.icon_detail else None,
        # illus 字段
        "illus_id":           r.illus_detail.illus_id   if r.illus_detail else None,
        "illus_category":     r.illus_detail.category   if r.illus_detail else None,
        "illus_tags":         r.illus_detail.tags        if r.illus_detail else None,
        "illus_version":      r.illus_detail.version    if r.illus_detail else None,
        "illus_theme":        r.illus_detail.theme      if r.illus_detail else None,
        # component 字段
        "cv_lib_file_key":    r.component_variant.lib_file_key    if r.component_variant else None,
        "cv_lib_name":        r.component_variant.lib_name        if r.component_variant else None,
        "cv_canvas_name":     r.component_variant.canvas_name     if r.component_variant else None,
        "cv_component_name":  r.component_variant.component_name  if r.component_variant else None,
        "cv_component_guid":  r.component_variant.component_guid  if r.component_variant else None,
        "cv_component_key":   r.component_variant.component_key   if r.component_variant else None,
        "cv_variant_name":    r.component_variant.name            if r.component_variant else None,
        "cv_variant_guid":    r.component_variant.guid            if r.component_variant else None,
        "cv_variant_key":     r.component_variant.variant_key     if r.component_variant else None,
        "cv_component_props": r.component_variant.component_props if r.component_variant else None,
    }


def _build_vector_text(r) -> Optional[str]:
    spec = get_registry().get(ResourceType(r.resource_type))
    if spec is None:
        return None
    try:
        return spec.build_text(r, {})
    except Exception:
        return None
