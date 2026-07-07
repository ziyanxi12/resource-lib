from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.resource import Resource, ResourceTag, ComponentVariant, ResourceIcon, ResourceIllus
from app.enums import ResourceType


# 表头筛选字段：对外字段名（与 _fmt 输出一致）→ (关联表, 列)
FILTER_FIELDS = {
    "cv_domain":         (ComponentVariant, ComponentVariant.domain),
    "cv_canvas_name":    (ComponentVariant, ComponentVariant.canvas_name),
    "cv_component_name": (ComponentVariant, ComponentVariant.component_name),
    "icon_category":     (ResourceIcon, ResourceIcon.category),
    "icon_group":        (ResourceIcon, ResourceIcon.group),
    "illus_category":    (ResourceIllus, ResourceIllus.category),
    "illus_version":     (ResourceIllus, ResourceIllus.version),
    "illus_theme":       (ResourceIllus, ResourceIllus.theme),
}

# 各资源类型可筛选的字段
FILTERABLE_BY_TYPE = {
    ResourceType.component: ["cv_domain", "cv_canvas_name", "cv_component_name"],
    ResourceType.icon:      ["icon_category", "icon_group"],
    ResourceType.illus:     ["illus_category", "illus_version", "illus_theme"],
}


def get_resources(
    db: Session,
    resource_type: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    filters: Optional[Dict[str, List[str]]] = None,
) -> Tuple[List[Resource], int]:
    query = db.query(Resource).filter(Resource.is_deleted == 0)

    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Resource.name.like(pattern),
                Resource.description.like(pattern),
            )
        )

    if filters:
        joined = set()
        for field, values in filters.items():
            if not values or field not in FILTER_FIELDS:
                continue
            model, column = FILTER_FIELDS[field]
            if model not in joined:
                query = query.join(model, model.resource_id == Resource.id)
                joined.add(model)
            query = query.filter(column.in_(values))

    total = query.count()
    items = (
        query.order_by(Resource.sort_order.desc(), Resource.created_at.desc())
             .offset((page - 1) * limit)
             .limit(limit)
             .all()
    )
    return items, total


def get_filter_options(db: Session, resource_type: int) -> Dict[str, List[str]]:
    """返回指定类型各可筛选字段的去重取值，供前端表头筛选项使用"""
    fields = FILTERABLE_BY_TYPE.get(ResourceType(resource_type), [])
    options: Dict[str, List[str]] = {}
    for field in fields:
        model, column = FILTER_FIELDS[field]
        rows = (
            db.query(column)
              .join(Resource, model.resource_id == Resource.id)
              .filter(Resource.is_deleted == 0, column.isnot(None), column != "")
              .distinct()
              .order_by(column)
              .all()
        )
        options[field] = [row[0] for row in rows]
    return options


def get_resource_by_id(db: Session, resource_id: int) -> Optional[Resource]:
    return db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.is_deleted == 0,
    ).first()


def get_categories_with_counts(db: Session) -> List[dict]:
    rows = (
        db.query(Resource.resource_type, func.count(Resource.id))
          .filter(Resource.is_deleted == 0)
          .group_by(Resource.resource_type)
          .all()
    )
    return [
        {
            "type":    ResourceType(rt).name,
            "type_id": rt,
            "label":   ResourceType(rt).label,
            "count":   count,
        }
        for rt, count in rows
    ]


def get_all_by_type(db: Session, resource_type: int) -> Tuple[List[Resource], int]:
    items = (
        db.query(Resource)
          .filter(Resource.is_deleted == 0, Resource.resource_type == resource_type)
          .order_by(Resource.sort_order.desc(), Resource.created_at.desc())
          .all()
    )
    return items, len(items)



def upsert_resource(db: Session, data: dict) -> Tuple[Resource, bool]:
    """按 (name, resource_type) 做 UPSERT，用于同步类操作（组件、图标、插画）。"""
    existing = db.query(Resource).filter(
        Resource.name == data["name"],
        Resource.resource_type == data["resource_type"],
        Resource.is_deleted == 0,
    ).first()

    if existing:
        for key, value in data.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        resource = Resource(**data)
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource, True


def create_resource(db: Session, data: dict) -> Resource:
    """直接插入新资源，用于上传类操作（图片、模版）。"""
    resource = Resource(**data)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def update_resource(db: Session, resource_id: int, data: dict) -> Optional[Resource]:
    resource = get_resource_by_id(db, resource_id)
    if not resource:
        return None
    for key, value in data.items():
        if hasattr(resource, key):
            setattr(resource, key, value)
    db.commit()
    db.refresh(resource)
    return resource


def soft_delete_resource(db: Session, resource_id: int) -> bool:
    resource = get_resource_by_id(db, resource_id)
    if not resource:
        return False
    resource.is_deleted = 1
    db.commit()
    return True


def update_tags(db: Session, resource_id: int, tags: List[str]) -> None:
    db.query(ResourceTag).filter(ResourceTag.resource_id == resource_id).delete()
    for tag in tags:
        db.add(ResourceTag(resource_id=resource_id, tag=tag.strip()))
    db.commit()


def get_all_data_ids(db: Session, resource_type: ResourceType) -> List[str]:
    """
    从数据库获取指定类型的所有 data_id
    
    返回格式：
    - component: [variant_key1, variant_key2, ...]
    - icon: [str(icon_id1), str(icon_id2), ...]
    - illus: [str(illus_id1), str(illus_id2), ...]
    - template/image: [str(resource.id1), str(resource.id2), ...]
    """
    from app.models.resource import ComponentVariant, ResourceIcon, ResourceIllus
    
    resources = db.query(Resource).filter(
        Resource.resource_type == resource_type,
        Resource.is_deleted == 0
    ).all()
    
    data_ids = []
    for r in resources:
        if resource_type == ResourceType.component:
            if r.component_variant:
                data_ids.append(r.component_variant.variant_key)
        elif resource_type == ResourceType.icon:
            if r.icon_detail:
                data_ids.append(str(r.icon_detail.icon_id))
        elif resource_type == ResourceType.illus:
            if r.illus_detail:
                data_ids.append(str(r.illus_detail.illus_id))
        else:  # template, image
            data_ids.append(str(r.id))
    
    return data_ids
