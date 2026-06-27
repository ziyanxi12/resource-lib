from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.resource import Resource, ResourceTag
from app.enums import ResourceType


def get_resources(
    db: Session,
    resource_type: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
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

    total = query.count()
    items = (
        query.order_by(Resource.sort_order.desc(), Resource.created_at.desc())
             .offset((page - 1) * limit)
             .limit(limit)
             .all()
    )
    return items, total


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


def bulk_upsert_resources(db: Session, items: List[dict], resource_type: int) -> dict:
    """批量 upsert，按 (name, resource_type) 做幂等键。
    返回 {name: (Resource, is_new)}，调用方负责最终 commit。
    """
    if not items:
        return {}

    names = list({d["name"] for d in items})
    existing_rows = db.query(Resource).filter(
        Resource.resource_type == resource_type,
        Resource.name.in_(names),
        Resource.is_deleted == 0,
    ).all()
    existing_map = {r.name: r for r in existing_rows}

    result: dict = {}
    for d in items:
        name = d["name"]
        if name in result:
            continue
        if name in existing_map:
            row = existing_map[name]
            for k, v in d.items():
                if hasattr(row, k) and v is not None:
                    setattr(row, k, v)
            result[name] = (row, False)
        else:
            row = Resource(**d)
            db.add(row)
            result[name] = (row, True)

    db.flush()
    return result


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
