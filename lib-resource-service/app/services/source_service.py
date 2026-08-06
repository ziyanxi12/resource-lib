import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.resource import ResourceSource, ResourceGroup, Resource

logger = logging.getLogger(__name__)


def get_sources(
    db: Session,
    resource_type: Optional[int] = None,
    is_active: Optional[int] = None,
    include_deleted: bool = False,
) -> List[ResourceSource]:
    query = db.query(ResourceSource)
    
    if not include_deleted:
        query = query.filter(ResourceSource.is_active == 1)
    
    if resource_type is not None:
        query = query.filter(ResourceSource.resource_type == resource_type)
    
    if is_active is not None:
        query = query.filter(ResourceSource.is_active == is_active)
    
    return query.order_by(ResourceSource.created_at.desc()).all()


def get_deleted_sources(
    db: Session,
    resource_type: Optional[int] = None,
) -> List[ResourceSource]:
    query = db.query(ResourceSource).filter(ResourceSource.is_active == 0)
    
    if resource_type is not None:
        query = query.filter(ResourceSource.resource_type == resource_type)
    
    return query.order_by(ResourceSource.updated_at.desc()).all()


def get_source_by_id(db: Session, source_id: int) -> Optional[ResourceSource]:
    return db.query(ResourceSource).filter(ResourceSource.id == source_id).first()


def create_source(db: Session, data: dict) -> ResourceSource:
    if "name" not in data:
        raise ValueError("name is required")
    
    source = ResourceSource(**data)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_source(db: Session, source_id: int, data: dict) -> Optional[ResourceSource]:
    source = get_source_by_id(db, source_id)
    if not source:
        return None
    
    for key, value in data.items():
        if hasattr(source, key):
            setattr(source, key, value)
    
    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, source_id: int) -> Optional[tuple]:
    """
    软删除来源（移入回收站），并级联软删除其下所有未删除资源。

    返回：(success, deleted_resource_ids, resource_type) 或 None（来源不存在）
    deleted_resource_ids: 本次被置 is_deleted=1 的资源 ID 列表，供 router 同步删向量
    """
    source = get_source_by_id(db, source_id)
    if not source:
        return None

    source.is_active = 0

    resources = db.query(Resource).filter(
        Resource.source_id == source_id,
        Resource.is_deleted == 0
    ).all()
    deleted_ids = [r.id for r in resources]

    if deleted_ids:
        db.query(Resource).filter(
            Resource.id.in_(deleted_ids)
        ).update({Resource.is_deleted: 1}, synchronize_session=False)

    db.commit()
    return (True, deleted_ids, source.resource_type)


def restore_source(db: Session, source_id: int) -> Optional[tuple]:
    """
    从回收站恢复来源，并级联恢复其下被软删除的资源。

    返回：(source, restored_resource_ids, resource_type) 或 None（来源不存在或不在回收站）
    restored_resource_ids: 本次被改回 is_deleted=0 的资源 ID 列表，供 router 重新 ingest 向量
    """
    source = get_source_by_id(db, source_id)
    if not source or source.is_active != 0:
        return None

    source.is_active = 1

    resources = db.query(Resource).filter(
        Resource.source_id == source_id,
        Resource.is_deleted == 1
    ).all()
    restored_ids = [r.id for r in resources]

    if restored_ids:
        db.query(Resource).filter(
            Resource.id.in_(restored_ids)
        ).update({Resource.is_deleted: 0}, synchronize_session=False)

    db.commit()
    db.refresh(source)
    return (source, restored_ids, source.resource_type)


def purge_source_data(db: Session, source_id: int) -> Optional[tuple]:
    """
    彻底清除回收站来源的资源向量数据（DB 记录保持软删除状态不动）。

    仅允许对已在回收站（is_active==0）的来源调用。
    返回：(resource_ids, resource_type) 或 None（来源不存在或不在回收站）
    resource_ids: 该来源下所有资源 ID（不过滤 is_deleted，删除来源时已全置 1）
    """
    source = get_source_by_id(db, source_id)
    if not source or source.is_active != 0:
        return None

    resources = db.query(Resource).filter(
        Resource.source_id == source_id
    ).all()
    resource_ids = [r.id for r in resources]

    return (resource_ids, source.resource_type)


def reset_vector_time_by_source(db: Session, source_id: int) -> int:
    """
    将指定来源下所有未删除资源的 vector_updated_at 置空，
    使其能被 sync_vectors_by_type 识别为待同步（用于恢复来源后强制重新 ingest）。
    返回：更新记录数
    """
    count = (
        db.query(Resource)
        .filter(
            Resource.source_id == source_id,
            Resource.is_deleted == 0,
        )
        .update({Resource.vector_updated_at: None}, synchronize_session=False)
    )
    db.commit()
    return count