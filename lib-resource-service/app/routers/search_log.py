"""
搜索日志采集查询接口
GET    /api/search-logs                    分页查看 vector_search_logs 表记录
DELETE /api/search-logs?resource_type=      按资源类型删除搜索日志
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.search_log import VectorSearchLog

router = APIRouter(prefix="/api/search-logs", tags=["搜索日志"])


def _fmt(log: VectorSearchLog):
    return {
        "id": log.id,
        "request_id": log.request_id,
        "api_path": log.api_path,
        "resource_type": log.resource_type,
        "search_mode": log.search_mode,
        "response_mode": log.response_mode,
        "top_k": log.top_k,
        "hybrid_weight": log.hybrid_weight,
        "query_count": log.query_count,
        "queries": log.queries,
        "filters": log.filters,
        "result_count": log.result_count,
        "status": log.status,
        "http_status": log.http_status,
        "error_message": log.error_message,
        "duration_ms": log.duration_ms,
        "client_ip": log.client_ip,
        "app_id": log.app_id,
        "user_agent": log.user_agent,
        "referer": log.referer,
        "business_data": log.business_data,
        "created_at": int(log.created_at.timestamp() * 1000) if log.created_at else None,
    }


@router.get("")
def list_search_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="success / error"),
    resource_type: Optional[str] = Query(None, description="component/icon/..."),
    db: Session = Depends(get_db),
):
    """分页查询搜索日志，按 created_at DESC 排序"""
    q = db.query(VectorSearchLog)
    if status:
        q = q.filter(VectorSearchLog.status == status)
    if resource_type:
        q = q.filter(VectorSearchLog.resource_type == resource_type)

    total = q.count()
    items = (
        q.order_by(VectorSearchLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "items": [_fmt(log) for log in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.delete("")
def delete_logs_by_type(
    resource_type: str = Query(..., description="要删除的资源类型，如 component/icon/illus/image/file"),
    db: Session = Depends(get_db),
):
    """按资源类型删除 vector_search_logs 日志记录。

    子表 search_log_results / search_log_filters 随 FK ondelete=CASCADE 自动删除。
    删除后请调用 POST /api/search-stats/refresh 重建统计汇总。
    """
    from app.services import search_stats_service
    result = search_stats_service.delete_logs_by_type(db, resource_type)
    return {"message": "删除完成", **result}
