import json
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.operation_log import OperationLog

logger = logging.getLogger(__name__)


def create_log(
    db: Session,
    *,
    source_id: Optional[int] = None,
    resource_type: Optional[int] = None,
    operator: str = "unknown",
    operator_account: str = "unknown",
    action: str = "",
    target_type: str = "",
    target_id: Optional[int] = None,
    target_name: Optional[str] = None,
    detail: Optional[dict] = None,
) -> None:
    """写入一条操作日志。静默执行，失败只 warning 不抛异常。"""
    try:
        log = OperationLog(
            source_id=source_id,
            resource_type=resource_type,
            operator=operator,
            operator_account=operator_account,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("写入操作日志失败: action=%s, error=%s", action, e)


def get_logs_by_source(
    db: Session,
    source_id: int,
    page: int = 1,
    limit: int = 20,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
) -> Tuple[List[OperationLog], int]:
    """按来源ID分页查询操作日志。"""
    query = db.query(OperationLog).filter(OperationLog.source_id == source_id)

    if action:
        query = query.filter(OperationLog.action == action)
    if target_type:
        query = query.filter(OperationLog.target_type == target_type)

    total = query.count()
    items = (
        query.order_by(OperationLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def format_log(log: OperationLog) -> dict:
    """序列化操作日志为 dict（遵循 epoch 毫秒规范）。"""
    return {
        "id": log.id,
        "source_id": log.source_id,
        "resource_type": log.resource_type,
        "operator": log.operator,
        "operator_account": log.operator_account,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "target_name": log.target_name,
        "detail": json.loads(log.detail) if log.detail else None,
        "created_at": int(log.created_at.timestamp() * 1000) if log.created_at else None,
    }
