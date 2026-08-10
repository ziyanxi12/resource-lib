"""
操作日志路由
GET /api/operation-logs?source_id=&page=&limit=&action=&target_type=
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import operation_log_service

router = APIRouter(prefix="/api/operation-logs", tags=["操作日志"])


@router.get("")
def list_logs(
    source_id: int = Query(..., description="来源ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    target_type: Optional[str] = Query(None, description="对象类型筛选"),
    db: Session = Depends(get_db),
):
    """获取指定来源的操作日志列表"""
    items, total = operation_log_service.get_logs_by_source(
        db, source_id, page, limit, action, target_type
    )
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [operation_log_service.format_log(log) for log in items],
    }
