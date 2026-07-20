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
) -> List[ResourceSource]:
    query = db.query(ResourceSource)
    
    if resource_type is not None:
        query = query.filter(ResourceSource.resource_type == resource_type)
    
    if is_active is not None:
        query = query.filter(ResourceSource.is_active == is_active)
    
    return query.order_by(ResourceSource.created_at.desc()).all()


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


def delete_source(db: Session, source_id: int) -> bool:
    source = get_source_by_id(db, source_id)
    if not source:
        return False
    
    # 检查是否有资源
    resource_count = db.query(Resource).filter(Resource.source_id == source_id).count()
    if resource_count > 0:
        raise ValueError(f"该来源下有 {resource_count} 条资源，无法删除。请先删除相关资源。")
    
    try:
        # 删除该来源下的所有分组（代码层面）
        db.query(ResourceGroup).filter(ResourceGroup.source_id == source_id).delete(synchronize_session=False)
        
        # 删除来源
        db.delete(source)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise ValueError("删除失败，请重试")