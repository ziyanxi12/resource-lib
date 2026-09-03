"""
初始化数据路由
POST /api/init/cleanup-orphan-groups - 清理孤儿分组
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import ResourceGroup, ResourceSource

router = APIRouter(prefix="/api/init", tags=["数据初始化"])


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
