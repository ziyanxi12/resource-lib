"""
初始化数据路由
仅支持组件集初始化，其他资源类型通过 ZIP 上传。
POST /api/init           - 导入组件集
POST /api/init/component - 导入组件集（同上）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import init_service

router = APIRouter(prefix="/api/init", tags=["数据初始化"])


@router.post("")
def init_all(db: Session = Depends(get_db)):
    """导入组件集数据"""
    return init_service.run_init_import(db)


@router.post("/component")
def init_component(db: Session = Depends(get_db)):
    """导入组件集数据"""
    return init_service.import_components(db)