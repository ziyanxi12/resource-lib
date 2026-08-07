"""
AI 补充描述任务路由

POST   /api/resources/ai-enrich              启动批量 AI 描述生成任务
GET    /api/resources/ai-enrich/{task_id}/status   查询任务进度
POST   /api/resources/ai-enrich/{task_id}/cancel   取消任务
"""

import logging
import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.enums import ResourceType
from app.services import ai_enrich_task_registry as task_registry
from app.services import ai_enrich_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["AI补充描述"])


@router.post("/ai-enrich")
def start_ai_enrich(
    type: str = Query(..., description="资源类型名，如 component、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    limit: Optional[int] = Query(None, ge=1, description="处理条数，默认全量"),
    concurrency: int = Query(1, ge=1, le=10, description="并发数，默认 1"),
    force: bool = Query(False, description="是否覆盖已生成的 AI 描述"),
    db: Session = Depends(get_db),
):
    """启动批量 AI 补充描述生成任务（异步，立即返回 task_id）"""
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    total = ai_enrich_service.count_pending(db, resource_type, source_id, force)
    if total == 0:
        return {"task_id": None, "total": 0, "message": "无待处理资源"}

    task = task_registry.create_task(type, source_id)

    def _run_enrich():
        enrich_db = SessionLocal()
        try:
            ai_enrich_service.enrich_batch(
                db=enrich_db,
                task_id=task.task_id,
                resource_type=resource_type,
                source_id=source_id,
                limit=limit,
                concurrency=concurrency,
                force=force,
            )
        except Exception as e:
            logger.exception("AI enrich 任务失败: task=%s", task.task_id)
            task_registry.update_task(
                task.task_id, status="failed", message=f"任务失败: {e}"
            )
        finally:
            enrich_db.close()

    threading.Thread(target=_run_enrich, daemon=True).start()

    return {"task_id": task.task_id, "total": total, "message": "AI 补充描述任务已启动"}


@router.get("/ai-enrich/{task_id}/status")
def get_ai_enrich_status(task_id: str):
    """查询 AI 补充描述任务进度"""
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return {
        "task_id": task.task_id,
        "status": task.status,
        "resource_type": task.resource_type,
        "source_id": task.source_id,
        "total": task.total,
        "processed": task.processed,
        "succeeded": task.succeeded,
        "failed": task.failed,
        "skipped": task.skipped,
        "errors": task.errors,
        "message": task.message,
    }


@router.post("/ai-enrich/{task_id}/cancel")
def cancel_ai_enrich(task_id: str):
    """取消 AI 补充描述任务"""
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法取消")
    task_registry.request_cancel(task_id)
    return {"message": "已请求取消"}
