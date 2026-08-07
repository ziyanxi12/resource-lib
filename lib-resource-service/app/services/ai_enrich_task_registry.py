"""
AI 补充描述任务状态注册表（进程内，线程安全）

用于批量生成 AI 描述的进度追踪与取消。
任务完成后保留 30 分钟，超时自动清理。
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AiEnrichTask:
    task_id: str
    resource_type: str
    source_id: Optional[int] = None
    status: str = "pending"           # pending / running / success / failed / cancelled
    total: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[dict] = field(default_factory=list)
    message: str = ""
    cancel_requested: bool = False
    started_at: float = 0.0
    finished_at: float = 0.0


_tasks: Dict[str, AiEnrichTask] = {}
_lock = threading.Lock()
_RETENTION_SECONDS = 1800  # 完成后保留 30 分钟


def create_task(resource_type: str, source_id: Optional[int] = None) -> AiEnrichTask:
    task = AiEnrichTask(
        task_id=uuid.uuid4().hex[:16],
        resource_type=resource_type,
        source_id=source_id,
        started_at=time.time(),
    )
    with _lock:
        _cleanup_expired_locked()
        _tasks[task.task_id] = task
    return task


def get_task(task_id: str) -> Optional[AiEnrichTask]:
    with _lock:
        return _tasks.get(task_id)


def update_task(task_id: str, **kwargs: Any) -> None:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        for k, v in kwargs.items():
            setattr(task, k, v)
        if kwargs.get("status") in ("success", "failed", "cancelled"):
            task.finished_at = time.time()
        _cleanup_expired_locked()


def increment_task(task_id: str, **fields: int) -> None:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        for k, v in fields.items():
            setattr(task, k, getattr(task, k) + v)


def add_error(task_id: str, resource_id: int, error: str) -> None:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task.errors.append({"resource_id": resource_id, "error": error})
        if len(task.errors) > 100:
            task.errors = task.errors[-100:]


def request_cancel(task_id: str) -> bool:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return False
        if task.status not in ("pending", "running"):
            return False
        task.cancel_requested = True
        return True


def is_cancelled(task_id: Optional[str]) -> bool:
    if not task_id:
        return False
    with _lock:
        task = _tasks.get(task_id)
        return task is not None and task.cancel_requested


def _cleanup_expired_locked() -> None:
    now = time.time()
    expired = [
        tid for tid, t in _tasks.items()
        if t.finished_at and (now - t.finished_at) > _RETENTION_SECONDS
    ]
    for tid in expired:
        del _tasks[tid]
