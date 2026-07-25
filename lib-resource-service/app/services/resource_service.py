import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.resource import Resource, ResourceTag, ResourceGroup
from app.enums import ResourceType

logger = logging.getLogger(__name__)


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
    tags: Optional[List[str]] = None,
) -> Tuple[List[Resource], int]:
    query = db.query(Resource).filter(Resource.is_deleted == 0)

    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)

    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    if group_id is not None:
        all_group_ids = _get_all_group_ids_with_descendants(db, group_id)
        query = query.filter(Resource.group_id.in_(all_group_ids))

    if tags:
        query = query.filter(
            Resource.id.in_(
                db.query(ResourceTag.resource_id)
                .filter(ResourceTag.tag.in_(tags))
            )
        )

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
        插入的 Resource 对象列表（含 id）
    """
    if not resources_data:
        return []
    
    for data in resources_data:
        if "source_id" not in data:
            raise ValueError("source_id is required")
    
    db.bulk_insert_mappings(Resource, resources_data)
    db.commit()
    
    source_ids = {d["source_id"] for d in resources_data}
    names = [d["name"] for d in resources_data]
    query = db.query(Resource).filter(
        Resource.source_id.in_(source_ids),
        Resource.name.in_(names),
        Resource.is_deleted == 0,
    ).order_by(Resource.id.desc()).limit(len(resources_data))
    
    return query.all()


def batch_insert_tags(db: Session, resource_tags: List[Tuple[int, List[str]]]) -> None:
    """
    批量插入标签
    
    Args:
        db: 数据库会话
        resource_tags: [(resource_id, ["tag1", "tag2"]), ...]
    """
    if not resource_tags:
        return
    
    resource_ids = [rid for rid, _ in resource_tags]
    db.query(ResourceTag).filter(ResourceTag.resource_id.in_(resource_ids)).delete()
    
    tag_mappings = []
    for resource_id, tags in resource_tags:
        for tag in tags:
            tag_mappings.append({
                "resource_id": resource_id,
                "tag": tag.strip(),
            })
    
    if tag_mappings:
        db.bulk_insert_mappings(ResourceTag, tag_mappings)
        db.commit()


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


def update_tags(db: Session, resource_id: int, tags: List[str]) -> None:
    db.query(ResourceTag).filter(ResourceTag.resource_id == resource_id).delete()
    for tag in tags:
        db.add(ResourceTag(resource_id=resource_id, tag=tag.strip()))
    db.commit()


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
    now = datetime.utcnow()
    logger.debug("批量更新向量同步时间: ids=%s, time=%s", resource_ids, now.isoformat())
    count = (
        db.query(Resource)
        .filter(Resource.id.in_(resource_ids))
        .update({Resource.vector_updated_at: now}, synchronize_session=False)
    )
    db.commit()
    logger.debug("更新完成: %d 条记录", count)
    return count


def build_vector_text(resource: Resource) -> str:
    """
    构造向量文本：name + description + tags + search_text
    """
    tags_str = ' '.join([t.tag for t in resource.tags])
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
) -> List[Dict]:
    """
    获取所有去重标签及使用数量，按使用量降序排列。

    返回：[{"tag": "标签名", "count": 5}, ...]
    """
    query = (
        db.query(ResourceTag.tag, func.count(ResourceTag.id).label("cnt"))
        .join(Resource, ResourceTag.resource_id == Resource.id)
        .filter(Resource.is_deleted == 0)
    )

    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)

    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    query = query.group_by(ResourceTag.tag).order_by(func.count(ResourceTag.id).desc())

    return [{"tag": row.tag, "count": row.cnt} for row in query.all()]


def _refresh_affected_resources(db: Session, resource_ids: List[int]) -> None:
    """对受影响资源重建 vector_text 并更新 data_updated_at"""
    if not resource_ids:
        return
    now = datetime.utcnow()
    resources = db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
    for res in resources:
        res.vector_text = build_vector_text(res)
        res.data_updated_at = now
    db.commit()


def rename_tag(
    db: Session,
    resource_type: Optional[int],
    source_id: Optional[int],
    old_tag: str,
    new_tag: str,
) -> int:
    """批量重命名标签（按 resource_type + source_id 限定作用域）。

    若新标签名在同作用域下已存在某些资源上，则对这些资源做合并去重：
    - 旧标签记录直接删除（该资源已有新标签，避免重复）
    - 仅旧标签独有的资源才 UPDATE 为新标签名

    返回受影响的资源数量。
    """
    base_resource_ids_subq = (
        db.query(Resource.id).filter(Resource.is_deleted == 0)
    )
    if resource_type is not None:
        base_resource_ids_subq = base_resource_ids_subq.filter(Resource.resource_type == resource_type)
    if source_id is not None:
        base_resource_ids_subq = base_resource_ids_subq.filter(Resource.source_id == source_id)

    old_res_ids = {
        rid for (rid,) in db.query(ResourceTag.resource_id)
        .join(Resource, ResourceTag.resource_id == Resource.id)
        .filter(ResourceTag.tag == old_tag)
        .filter(Resource.id.in_(base_resource_ids_subq))
        .all()
    }
    new_res_ids = {
        rid for (rid,) in db.query(ResourceTag.resource_id)
        .join(Resource, ResourceTag.resource_id == Resource.id)
        .filter(ResourceTag.tag == new_tag)
        .filter(Resource.id.in_(base_resource_ids_subq))
        .all()
    }

    affected = old_res_ids
    merge_ids = old_res_ids & new_res_ids
    pure_rename_ids = old_res_ids - new_res_ids

    if merge_ids:
        db.query(ResourceTag).filter(
            ResourceTag.tag == old_tag,
            ResourceTag.resource_id.in_(merge_ids),
        ).delete(synchronize_session=False)

    if pure_rename_ids:
        db.query(ResourceTag).filter(
            ResourceTag.tag == old_tag,
            ResourceTag.resource_id.in_(pure_rename_ids),
        ).update({ResourceTag.tag: new_tag}, synchronize_session=False)

    db.commit()
    _refresh_affected_resources(db, list(affected))
    logger.info("重命名标签: '%s' -> '%s', 受影响资源 %d 条", old_tag, new_tag, len(affected))
    return len(affected)


def delete_tag(
    db: Session,
    resource_type: Optional[int],
    source_id: Optional[int],
    tag: str,
) -> int:
    """批量删除标签（按 resource_type + source_id 限定作用域）。

    返回受影响的资源数量。
    """
    base_resource_ids_subq = (
        db.query(Resource.id).filter(Resource.is_deleted == 0)
    )
    if resource_type is not None:
        base_resource_ids_subq = base_resource_ids_subq.filter(Resource.resource_type == resource_type)
    if source_id is not None:
        base_resource_ids_subq = base_resource_ids_subq.filter(Resource.source_id == source_id)

    affected_ids = {
        rid for (rid,) in db.query(ResourceTag.resource_id)
        .join(Resource, ResourceTag.resource_id == Resource.id)
        .filter(ResourceTag.tag == tag)
        .filter(Resource.id.in_(base_resource_ids_subq))
        .all()
    }

    db.query(ResourceTag).filter(
        ResourceTag.tag == tag,
        ResourceTag.resource_id.in_(affected_ids),
    ).delete(synchronize_session=False)

    db.commit()
    _refresh_affected_resources(db, list(affected_ids))
    logger.info("删除标签: '%s', 受影响资源 %d 条", tag, len(affected_ids))
    return len(affected_ids)