"""
初始化数据路由
仅支持组件集初始化，其他资源类型通过 ZIP 上传。
POST /api/init           - 导入组件集
POST /api/init/component - 导入组件集（同上）
POST /api/init/cleanup-orphan-groups - 清理孤儿分组
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services import init_service
from app.models.resource import ResourceGroup, ResourceSource

router = APIRouter(prefix="/api/init", tags=["数据初始化"])


@router.post("")
def init_all(
    source_id: Optional[int] = Query(None, description="来源ID，不传则使用已存在的来源"),
    db: Session = Depends(get_db)
):
    """导入组件集数据"""
    return init_service.run_init_import(db, source_id=source_id)


@router.post("/component")
def init_component(
    source_id: Optional[int] = Query(None, description="来源ID，不传则使用已存在的来源"),
    skip_vector: bool = Query(False, description="是否跳过向量同步"),
    db: Session = Depends(get_db)
):
    """导入组件集数据"""
    return init_service.import_components(db, source_id=source_id, skip_vector=skip_vector)


@router.post("/cleanup-orphan-groups")
def cleanup_orphan_groups(db: Session = Depends(get_db)):
    """清理孤儿分组（source_id 不存在的分组）"""
    # 查询孤儿分组数量
    valid_source_ids = db.query(ResourceSource.id).subquery()
    count = db.query(ResourceGroup).filter(
        ResourceGroup.source_id.isnot(None),
        ~ResourceGroup.source_id.in_(valid_source_ids)
    ).count()
    
    # 删除孤儿分组
    db.query(ResourceGroup).filter(
        ResourceGroup.source_id.isnot(None),
        ~ResourceGroup.source_id.in_(valid_source_ids)
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return {"deleted": count, "message": f"已清理 {count} 条孤儿分组"}