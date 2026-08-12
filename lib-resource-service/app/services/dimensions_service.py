"""
资源宽高回填服务

核心功能：
1. 统计 width/height 缺失的资源数量（is_deleted=0）
2. 异步批量读取缩略图尺寸，用 bulk_update_mappings 分批回填
3. 通过 dimension_task_registry 追踪进度，支持取消
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.enums import ResourceType
from app.models.resource import Resource
from app.services import dimension_task_registry as task_registry
from app.services.image_meta_service import read_thumbnail_dimensions

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000


def _missing_query(
    db: Session,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
    group_id: Optional[int] = None,
):
    query = db.query(Resource).filter(
        Resource.is_deleted == 0,
        or_(Resource.width.is_(None), Resource.height.is_(None)),
    )
    if resource_type is not None:
        query = query.filter(Resource.resource_type == resource_type)
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)
    if group_id is not None:
        query = query.filter(Resource.group_id == group_id)
    return query


def count_missing(
    db: Session,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> int:
    """统计宽高缺失的资源数量（不 limit，不含软删除）"""
    return _missing_query(db, resource_type, source_id, group_id).count()


def count_missing_by_type(
    db: Session,
    source_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> List[dict]:
    """按资源类型分组统计宽高缺失数量"""
    query = db.query(
        Resource.resource_type,
        func.count(Resource.id).label("count"),
    ).filter(
        Resource.is_deleted == 0,
        or_(Resource.width.is_(None), Resource.height.is_(None)),
    )
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)
    if group_id is not None:
        query = query.filter(Resource.group_id == group_id)

    rows = query.group_by(Resource.resource_type).order_by(Resource.resource_type).all()
    return [
        {
            "resource_type": rt,
            "resource_type_name": ResourceType(rt).name,
            "count": count,
        }
        for rt, count in rows
    ]


def fill_missing_dimensions(
    db: Session,
    task_id: str,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
    group_id: Optional[int] = None,
    limit: Optional[int] = None,
    concurrency: int = 8,
) -> None:
    """
    批量回填宽高（在后台线程中执行）

    1. 查询缺失宽高的资源（仅取 id / width / height / thumbnail_path）
    2. ThreadPoolExecutor 并行读取缩略图尺寸
    3. bulk_update_mappings 按 chunk 批量回写，每 chunk 一次 commit
    """
    task_registry.update_task(task_id, status="running", message="正在查询待处理资源")

    query = _missing_query(db, resource_type, source_id, group_id)
    query = query.with_entities(
        Resource.id,
        Resource.width,
        Resource.height,
        Resource.thumbnail_path,
    ).order_by(Resource.id)
    if limit:
        query = query.limit(limit)
    rows = query.all()
    total = len(rows)

    if not rows:
        task_registry.update_task(
            task_id, status="success", total=0, processed=0,
            message="无待处理资源",
        )
        return

    task_registry.update_task(task_id, total=total, message=f"开始回填 {total} 条资源")
    logger.info(
        "宽高回填开始: task=%s total=%d concurrency=%d",
        task_id, total, concurrency,
    )

    processed = 0
    succeeded = 0
    skipped = 0

    def _read(thumb_path: Optional[str]) -> Optional[Tuple[float, float]]:
        return read_thumbnail_dimensions(thumb_path)

    try:
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
            for start in range(0, total, CHUNK_SIZE):
                if task_registry.is_cancelled(task_id):
                    break
                chunk = rows[start:start + CHUNK_SIZE]
                dims_list = list(executor.map(_read, [r.thumbnail_path for r in chunk]))

                mappings = []
                for r, dims in zip(chunk, dims_list):
                    if dims is None:
                        skipped += 1
                        continue
                    mapping = {"id": r.id}
                    if r.width is None:
                        mapping["width"] = dims[0]
                    if r.height is None:
                        mapping["height"] = dims[1]
                    if "width" not in mapping and "height" not in mapping:
                        continue
                    mappings.append(mapping)

                if mappings:
                    db.bulk_update_mappings(Resource, mappings)
                    db.commit()
                    succeeded += len(mappings)
                    logger.info(
                        "宽高回填 chunk: task=%s 已回填 %d 条", task_id, len(mappings)
                    )

                processed += len(chunk)
                task_registry.update_task(
                    task_id,
                    processed=processed,
                    succeeded=succeeded,
                    skipped=skipped,
                    message=f"处理 {processed}/{total}",
                )
    except Exception as e:
        db.rollback()
        logger.exception("宽高回填异常: task=%s", task_id)
        task_registry.update_task(task_id, status="failed", message=f"任务异常: {e}")
        return

    final_status = "cancelled" if task_registry.is_cancelled(task_id) else "success"
    message = f"完成：成功回填 {succeeded}，跳过 {skipped}，共 {total}"
    task_registry.update_task(task_id, status=final_status, message=message)

    logger.info(
        "宽高回填完成: task=%s status=%s total=%d succeeded=%d skipped=%d",
        task_id, final_status, total, succeeded, skipped,
    )