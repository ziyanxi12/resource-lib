import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.resource import Resource, ResourceGroup
from app.enums import ResourceType

logger = logging.getLogger(__name__)


def normalize_tags(tags: Optional[List[str]]) -> List[str]:
    """规范化标签列表：strip + 去空 + 去重（保持顺序）"""
    if not tags:
        return []
    seen = []
    for t in tags:
        t = (t or '').strip()
        if t and t not in seen:
            seen.append(t)
    return seen


def _get_all_group_ids_with_descendants(db: Session, group_id: int) -> List[int]:
    ids = [group_id]
    children = db.query(ResourceGroup).filter(ResourceGroup.parent_id == group_id).all()
    for child in children:
        ids.extend(_get_all_group_ids_with_descendants(db, child.id))
    return ids


def get_resources(
    db: Session,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    group_id: Optional[int] = None,
) -> Tuple[List[Resource], int]:
    query = db.query(Resource).filter(Resource.is_deleted == 0)

    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)

    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    if group_id is not None:
        all_group_ids = _get_all_group_ids_with_descendants(db, group_id)
        query = query.filter(Resource.group_id.in_(all_group_ids))

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Resource.name.like(pattern),
                Resource.description.like(pattern),
                Resource.search_text.like(pattern),
            )
        )

    total = query.count()
    items = (
        query.order_by(Resource.created_at.desc())
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


def create_resource(db: Session, data: dict) -> Resource:
    if "source_id" not in data:
        raise ValueError("source_id is required")
    
    resource = Resource(**data)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def batch_create_resources(db: Session, resources_data: List[dict]) -> List[Resource]:
    """
    批量创建资源
    
    Args:
        db: 数据库会话
        resources_data: 资源数据列表
    
    Returns:
        插入的 Resource 对象列表（含 id），顺序与 resources_data 严格一致
    """
    if not resources_data:
        return []
    
    for data in resources_data:
        if "source_id" not in data:
            raise ValueError("source_id is required")
    
    resources = [Resource(**data) for data in resources_data]
    db.add_all(resources)
    db.flush()
    return resources


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


def batch_soft_delete_by_filters(
    db: Session,
    resource_type: int,
    source_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> Tuple[List[int], int]:
    """
    按条件批量软删除资源
    
    返回：(被删除的资源ID列表, 删除数量)
    """
    query = db.query(Resource).filter(
        Resource.resource_type == resource_type,
        Resource.is_deleted == 0,
    )
    
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)
    
    if group_id is not None:
        query = query.filter(Resource.group_id == group_id)
    
    resources = query.all()
    deleted_ids = [r.id for r in resources]
    
    if deleted_ids:
        db.query(Resource).filter(Resource.id.in_(deleted_ids)).update(
            {Resource.is_deleted: 1},
            synchronize_session=False
        )
        db.commit()
    
    return deleted_ids, len(deleted_ids)


def batch_soft_delete_by_ids(
    db: Session,
    ids: List[int],
) -> Tuple[List[int], int]:
    """
    按 ID 列表批量软删除资源

    返回：(被删除的资源ID列表, 删除数量)
    """
    if not ids:
        return [], 0

    resources = db.query(Resource).filter(
        Resource.id.in_(ids),
        Resource.is_deleted == 0,
    ).all()
    deleted_ids = [r.id for r in resources]

    if deleted_ids:
        db.query(Resource).filter(Resource.id.in_(deleted_ids)).update(
            {Resource.is_deleted: 1},
            synchronize_session=False
        )
        db.commit()

    return deleted_ids, len(deleted_ids)


def batch_move_group(
    db: Session,
    ids: List[int],
    group_id: int,
) -> Tuple[List[int], int]:
    """
    批量移动资源到指定分组

    返回：(被移动的资源ID列表, 移动数量)
    """
    if not ids:
        return [], 0

    resources = db.query(Resource).filter(
        Resource.id.in_(ids),
        Resource.is_deleted == 0,
    ).all()
    moved_ids = [r.id for r in resources]

    if moved_ids:
        db.query(Resource).filter(Resource.id.in_(moved_ids)).update(
            {Resource.group_id: group_id},
            synchronize_session=False
        )
        db.commit()

    return moved_ids, len(moved_ids)


def get_resources_need_sync(db: Session, resource_type: int, source_id: int = None) -> Tuple[List[Resource], int]:
    """
    获取需要同步向量的资源（vector_updated_at < data_updated_at 或 vector_updated_at 为空）
    返回：(待同步资源列表, 总数)
    """
    logger.debug("查询待同步资源: type=%d, source_id=%s, 条件=vector_updated_at < data_updated_at OR NULL", resource_type, source_id)
    query = (
        db.query(Resource)
        .filter(
            Resource.resource_type == resource_type,
            Resource.is_deleted == 0,
            or_(
                Resource.vector_updated_at.is_(None),
                Resource.vector_updated_at < Resource.data_updated_at
            )
        )
    )
    
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)
    
    resources = query.order_by(Resource.data_updated_at.asc()).all()
    logger.debug("查询到 %d 条待同步资源: ids=%s", len(resources), [r.id for r in resources])
    return resources, len(resources)


def batch_update_vector_time(db: Session, resource_ids: List[int]) -> int:
    """
    批量更新资源的向量同步时间
    返回：更新的记录数
    """
    if not resource_ids:
        logger.debug("无资源需要更新向量时间")
        return 0
    now = datetime.now()
    logger.debug("批量更新向量同步时间: ids=%s, time=%s", resource_ids[:10], now.isoformat())
    # 分块更新，避免 SQLite IN 子句参数上限 (默认 999)
    chunk_size = 500
    total_count = 0
    for i in range(0, len(resource_ids), chunk_size):
        chunk = resource_ids[i:i + chunk_size]
        count = (
            db.query(Resource)
            .filter(Resource.id.in_(chunk))
            .update({Resource.vector_updated_at: now}, synchronize_session=False)
        )
        total_count += count
    db.commit()
    logger.debug("更新完成: %d 条记录", total_count)
    return total_count


def build_vector_text(resource: Resource) -> str:
    """
    构造向量文本：name + description + tags + search_text
    """
    tags_str = ' '.join(resource.tags or [])
    parts = [
        resource.name or '',
        resource.description or '',
        tags_str,
        resource.search_text or ''
    ]
    vector_text = ' '.join(filter(None, parts))
    return ' '.join(vector_text.split())


def get_all_tags(
    db: Session,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
) -> List[str]:
    """获取去重标签列表（按字母序排列）。"""
    query = db.query(Resource.tags).filter(Resource.is_deleted == 0)
    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    seen = []
    for (tags,) in query.all():
        for t in (tags or []):
            if t not in seen:
                seen.append(t)
    return sorted(seen)