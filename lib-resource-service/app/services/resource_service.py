"""
通用资源 CRUD 服务
提供 resources 表和 resource_tags 表的基础操作，供各类型 service 复用。
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.resource import Resource, ResourceTag


def get_resources(
    db: Session,
    resource_type: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Resource], int]:
    """
    查询资源列表。
    支持：按 resource_type 过滤 / 关键词搜索（name、english_name、description）/ 分页。
    默认排序：sort_order 降序 → created_at 降序。
    """
    query = db.query(Resource).filter(Resource.is_deleted == 0)

    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Resource.name.like(pattern),
                Resource.english_name.like(pattern),
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
    """查询单个资源（已软删除的不返回）"""
    return db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.is_deleted == 0,
    ).first()


def upsert_resource(db: Session, data: dict) -> Tuple[Resource, bool]:
    """
    按 unique_key 插入或更新资源（UPSERT）。
    返回 (resource, is_new)：is_new=True 表示新增，False 表示更新。
    """
    existing = db.query(Resource).filter(
        Resource.unique_key == data["unique_key"]
    ).first()

    if existing:
        # 更新：只覆盖 data 中明确传入的非 None 字段
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


def update_resource(db: Session, resource_id: int, data: dict) -> Optional[Resource]:
    """更新资源元数据，返回更新后的对象；资源不存在时返回 None。"""
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
    """软删除：将 is_deleted 置为 1，数据保留在库中。"""
    resource = get_resource_by_id(db, resource_id)
    if not resource:
        return False

    resource.is_deleted = 1
    db.commit()
    return True


def update_tags(db: Session, resource_id: int, tags: List[str]) -> None:
    """替换资源的全部标签（先清空，再批量插入）。"""
    db.query(ResourceTag).filter(ResourceTag.resource_id == resource_id).delete()
    for tag in tags:
        db.add(ResourceTag(resource_id=resource_id, tag=tag.strip()))
    db.commit()
