"""
导入任务状态查询与取消
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ResourceType
from app.services import import_task_registry
from app.services import operation_log_service
from app.services.operator import get_operator

router = APIRouter(prefix="/api/import", tags=["导入任务"])


@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """查询导入任务状态"""
    task = import_task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return {
        "task_id": task.task_id,
        "status": task.status,
        "phase": task.phase,
        "phase_label": task.phase_label,
        "groups_created": task.groups_created,
        "resources_created": task.resources_created,
        "errors": task.errors,
        "message": task.message,
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, request: Request, db: Session = Depends(get_db)):
    """请求取消导入任务"""
    task = import_task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法取消")
    import_task_registry.request_cancel(task_id)

    account, name = get_operator(request)
    try:
        rt_int = int(ResourceType.from_name(task.resource_type))
    except (KeyError, ValueError):
        rt_int = None
    operation_log_service.create_log(
        db,
        source_id=task.source_id,
        resource_type=rt_int,
        operator=name,
        operator_account=account,
        action="batch_import_cancel",
        target_type="resource",
        detail={"task_id": task_id},
    )

    return {"message": "已请求取消"}
