"""
宽高回填任务路由

GET  /api/resources/dimensions/missing                  查询宽高缺失数量（按类型分组）
POST /api/resources/fill-dimensions                     启动异步批量回填任务
GET  /api/resources/fill-dimensions/{task_id}/status    查询任务进度
POST /api/resources/fill-dimensions/{task_id}/cancel    取消任务
"""

import logging
import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.enums import ResourceType
from app.services import dimension_task_registry as task_registry
from app.services import dimensions_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["宽高回填"])


def _resolve_type(type_name: Optional[str]) -> Optional[int]:
    if not type_name:
        return None
    try:
        return int(ResourceType.from_name(type_name))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type_name}")


@router.get("/dimensions/missing")
def get_missing_dimensions(
    type: Optional[str] = Query(None, description="资源类型名，如 component、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    group_id: Optional[int] = Query(None, description="分组ID筛选"),
    db: Session = Depends(get_db),
):
    """统计宽高缺失的资源数量（不含软删除），未指定 type 时按类型分组返回"""
    resource_type = _resolve_type(type)

    if resource_type is not None:
        total = dimensions_service.count_missing(db, resource_type, source_id, group_id)
        items = [
            {
                "resource_type": resource_type,
                "resource_type_name": ResourceType(resource_type).name,
                "count": total,
            }
        ]
    else:
        items = dimensions_service.count_missing_by_type(db, source_id, group_id)
        total = sum(item["count"] for item in items)

    return {"total": total, "items": items}


@router.post("/fill-dimensions")
def start_fill_dimensions(
    type: Optional[str] = Query(None, description="资源类型名，如 component、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    group_id: Optional[int] = Query(None, description="分组ID筛选"),
    limit: Optional[int] = Query(None, ge=1, description="处理条数，默认全量"),
    concurrency: int = Query(8, ge=1, le=32, description="读取缩略图并发数"),
    db: Session = Depends(get_db),
):
    """启动批量宽高回填任务（异步，立即返回 task_id）"""
    resource_type = _resolve_type(type)

    total = dimensions_service.count_missing(db, resource_type, source_id, group_id)
    if total == 0:
        return {"task_id": None, "total": 0, "message": "无待处理资源"}

    task = task_registry.create_task(type, source_id, group_id)

    def _run_fill():
        fill_db = SessionLocal()
        try:
            dimensions_service.fill_missing_dimensions(
                db=fill_db,
                task_id=task.task_id,
                resource_type=resource_type,
                source_id=source_id,
                group_id=group_id,
                limit=limit,
                concurrency=concurrency,
            )
        except Exception as e:
            logger.exception("宽高回填任务失败: task=%s", task.task_id)
            task_registry.update_task(
                task.task_id, status="failed", message=f"任务失败: {e}"
            )
        finally:
            fill_db.close()

    threading.Thread(target=_run_fill, daemon=True).start()

    return {
        "task_id": task.task_id,
        "total": total,
        "filter": {"type": type, "source_id": source_id, "group_id": group_id},
        "message": "宽高回填任务已启动",
    }


@router.get("/fill-dimensions/{task_id}/status")
def get_fill_dimensions_status(task_id: str):
    """查询宽高回填任务进度"""
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return {
        "task_id": task.task_id,
        "status": task.status,
        "resource_type": task.resource_type,
        "source_id": task.source_id,
        "group_id": task.group_id,
        "total": task.total,
        "processed": task.processed,
        "succeeded": task.succeeded,
        "skipped": task.skipped,
        "failed": task.failed,
        "errors": task.errors,
        "message": task.message,
    }


@router.post("/fill-dimensions/{task_id}/cancel")
def cancel_fill_dimensions(task_id: str):
    """取消宽高回填任务"""
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法取消")
    task_registry.request_cancel(task_id)
    return {"message": "已请求取消"}