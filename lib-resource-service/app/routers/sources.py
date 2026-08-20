"""
来源管理路由
"""

import logging
import os
import tempfile
import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.schemas.source import SourceCreate, SourceUpdate
from app.services import source_service, import_service, import_task_registry, vector_sync_service
from app.services import operation_log_service
from app.services.operator import get_operator
from app.services.user_service import resolve_display_names
from app.enums import ResourceType
from app.clients import vector_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sources", tags=["来源管理"])


def _format_source(s, display_map=None):
    def _display(val):
        if not val:
            return val
        if display_map:
            return display_map.get(val, val)
        return val
    return {
        "id": s.id,
        "name": s.name,
        "resource_type": s.resource_type,
        "is_sync_source": s.is_sync_source,
        "config": s.config,
        "is_active": s.is_active,
        "created_by": _display(s.created_by),
        "updated_by": _display(s.updated_by),
        "created_at": int(s.created_at.timestamp() * 1000) if s.created_at else None,
        "updated_at": int(s.updated_at.timestamp() * 1000) if s.updated_at else None,
    }


@router.get("")
def list_sources(
    type: Optional[str] = Query(None, description="资源类型名，如 component、icon、illus"),
    is_active: Optional[int] = Query(None, description="是否启用筛选"),
    db: Session = Depends(get_db),
):
    """获取来源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    
    sources = source_service.get_sources(db, resource_type=resource_type_int, is_active=is_active)
    accounts = set()
    for s in sources:
        if s.created_by: accounts.add(s.created_by)
        if s.updated_by: accounts.add(s.updated_by)
    display_map = resolve_display_names(db, list(accounts))
    return {"items": [_format_source(s, display_map) for s in sources]}


@router.get("/trash")
def list_trash_sources(
    type: Optional[str] = Query(None, description="资源类型名"),
    db: Session = Depends(get_db),
):
    """获取回收站中的来源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    
    sources = source_service.get_deleted_sources(db, resource_type=resource_type_int)
    accounts = set()
    for s in sources:
        if s.created_by: accounts.add(s.created_by)
        if s.updated_by: accounts.add(s.updated_by)
    display_map = resolve_display_names(db, list(accounts))
    return {"items": [_format_source(s, display_map) for s in sources]}


@router.get("/{source_id}")
def get_source(source_id: int, db: Session = Depends(get_db)):
    """获取来源详情"""
    source = source_service.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    display_map = resolve_display_names(db, [x for x in [source.created_by, source.updated_by] if x])
    return _format_source(source, display_map)


@router.post("")
def create_source(body: SourceCreate, request: Request, db: Session = Depends(get_db)):
    """创建来源"""
    try:
        resource_type = ResourceType.from_name(body.type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {body.type}")
    
    account, name = get_operator(request)
    create_data = {
        "name": body.name,
        "resource_type": int(resource_type),
        "is_sync_source": body.is_sync_source,
        "config": body.config,
        "is_active": body.is_active,
        "created_by": account,
        "updated_by": account,
    }
    
    try:
        source = source_service.create_source(db, create_data)
        operation_log_service.create_log(
            db,
            source_id=source.id,
            resource_type=int(resource_type),
            operator=name,
            operator_account=account,
            action="create",
            target_type="source",
            target_id=source.id,
            target_name=source.name,
        )
        display_map = resolve_display_names(db, [account])
        return _format_source(source, display_map)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{source_id}")
def update_source(source_id: int, body: SourceUpdate, request: Request, db: Session = Depends(get_db)):
    """更新来源"""
    account, name = get_operator(request)
    data = body.model_dump(exclude_unset=True)
    if body.name is not None:
        data["updated_by"] = account
    try:
        source = source_service.update_source(db, source_id, data)
        if not source:
            raise HTTPException(status_code=404, detail="来源不存在")
        operation_log_service.create_log(
            db,
            source_id=source.id,
            resource_type=source.resource_type,
            operator=name,
            operator_account=account,
            action="update",
            target_type="source",
            target_id=source.id,
            target_name=source.name,
            detail={"fields": list(data.keys())},
        )
        display_map = resolve_display_names(db, [x for x in [source.created_by, source.updated_by] if x])
        return _format_source(source, display_map)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{source_id}")
def delete_source(source_id: int, request: Request, db: Session = Depends(get_db)):
    """软删除来源（移入回收站），并同步删除关联资源的向量数据"""
    source = source_service.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    s_name = source.name
    s_type = source.resource_type

    result = source_service.delete_source(db, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="来源不存在")

    _success, deleted_ids, resource_type = result

    if settings.VECTOR_SERVICE_ENABLED and deleted_ids and resource_type is not None:
        vec_type = ResourceType(resource_type).vec_type
        try:
            vector_client.batch_delete(vec_type, [str(i) for i in deleted_ids])
        except Exception as e:
            logger.warning("删除来源时向量批量删除异常 (source_id=%s, type=%s): %s", source_id, vec_type, e)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=source_id,
        resource_type=s_type,
        operator=name,
        operator_account=account,
        action="delete",
        target_type="source",
        target_id=source_id,
        target_name=s_name,
        detail={"deleted_resources": len(deleted_ids)},
    )

    return {"message": "已移入回收站"}


@router.post("/{source_id}/restore")
def restore_source(source_id: int, request: Request, db: Session = Depends(get_db)):
    """从回收站恢复来源，并重新 ingest 关联资源的向量数据"""
    result = source_service.restore_source(db, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="来源不存在或不在回收站中")

    source, restored_ids, resource_type = result

    if (
        settings.VECTOR_SERVICE_ENABLED
        and restored_ids
        and resource_type is not None
    ):
        # 置空 vector_updated_at，使 sync_vectors_by_type 强制识别为待同步
        source_service.reset_vector_time_by_source(db, source_id)
        try:
            vector_sync_service.sync_vectors_by_type(
                db, ResourceType(resource_type), source_id=source_id
            )
        except Exception as e:
            logger.warning("恢复来源时向量重新入库异常 (source_id=%s): %s", source_id, e)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=source_id,
        resource_type=source.resource_type,
        operator=name,
        operator_account=account,
        action="restore",
        target_type="source",
        target_id=source.id,
        target_name=source.name,
        detail={"restored_resources": len(restored_ids)},
    )

    display_map = resolve_display_names(db, [x for x in [source.created_by, source.updated_by] if x])
    return _format_source(source, display_map)


@router.delete("/{source_id}/purge")
def purge_source_data(source_id: int, db: Session = Depends(get_db)):
    """彻底清除回收站来源的资源向量数据（DB 记录保持软删除状态不动）"""
    result = source_service.purge_source_data(db, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="来源不存在或不在回收站中")

    resource_ids, resource_type = result

    if settings.VECTOR_SERVICE_ENABLED and resource_ids and resource_type is not None:
        vec_type = ResourceType(resource_type).vec_type
        try:
            vector_client.batch_delete(vec_type, [str(i) for i in resource_ids])
        except Exception as e:
            logger.warning("purge 来源时向量批量删除异常 (source_id=%s, type=%s): %s", source_id, vec_type, e)

    return {"purged": len(resource_ids), "source_id": source_id}


@router.post("/{source_id}/import")
async def full_batch_import(
    source_id: int,
    request: Request,
    type: str = Query(..., description="资源类型名，如 icon、illus 等"),
    db: Session = Depends(get_db),
):
    """全量批量导入：上传 ZIP 包，在指定来源下递归创建分组及资源。
    立即返回 task_id，后台线程执行导入，通过 GET /api/import/tasks/{task_id}/status 轮询进度。
    """
    # 校验资源类型
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    # 校验来源存在
    source = source_service.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    if source.resource_type != int(resource_type):
        raise HTTPException(
            status_code=400,
            detail=f"来源类型不匹配：来源为 {ResourceType(source.resource_type).name}，请求为 {type}",
        )

    # 流式接收 ZIP → 写临时文件（避免大文件全量读入内存）
    tmp_dir = os.path.join(settings.FILE_ROOT_DIR, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_fd, zip_path = tempfile.mkstemp(suffix=".zip", dir=tmp_dir)
    try:
        with os.fdopen(tmp_fd, "wb") as tmp_f:
            async for chunk in request.stream():
                if chunk:
                    tmp_f.write(chunk)
        file_size = os.path.getsize(zip_path)
        if file_size == 0:
            os.unlink(zip_path)
            raise HTTPException(status_code=400, detail="未接收到文件内容")
        logger.info("[import] ZIP 已保存: %s, size=%s bytes", zip_path, file_size)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(zip_path):
            os.unlink(zip_path)
        logger.warning("[import] 流式接收异常: %s", e)
        raise HTTPException(status_code=400, detail=f"接收文件失败: {e}")

    # 提取操作人信息（在请求线程中，传入后台线程）
    account, op_name = get_operator(request)
    logger.info("[import] source_id=%s type=%s file_size=%s operator: account=%s, name=%s",
                source_id, type, file_size, account, op_name)

    # 创建任务
    task = import_task_registry.create_task(source_id, type)

    # 后台线程执行导入（独立 session，不阻塞请求）
    def _run_import():
        import_db = SessionLocal()
        try:
            import_service.full_batch_import(
                import_db,
                source_id=source_id,
                resource_type=resource_type,
                zip_path=zip_path,
                task_id=task.task_id,
                created_by=account,
            )
            operation_log_service.create_log(
                import_db,
                source_id=source_id,
                resource_type=int(resource_type),
                operator=op_name,
                operator_account=account,
                action="batch_import",
                target_type="resource",
                detail={
                    "task_id": task.task_id,
                    "type": type,
                    "status": "success",
                    "groups_created": import_task_registry.get_task(task.task_id).groups_created,
                    "resources_created": import_task_registry.get_task(task.task_id).resources_created,
                },
            )
        except import_service.ImportCancelled:
            import_task_registry.update_task(
                task.task_id, status="cancelled", phase_label="已取消"
            )
            operation_log_service.create_log(
                import_db,
                source_id=source_id,
                resource_type=int(resource_type),
                operator=op_name,
                operator_account=account,
                action="batch_import",
                target_type="resource",
                detail={"task_id": task.task_id, "type": type, "status": "cancelled"},
            )
            logger.info("导入已取消: task=%s", task.task_id)
        except Exception as e:
            import_task_registry.update_task(
                task.task_id, status="failed", message=str(e), phase_label="失败"
            )
            operation_log_service.create_log(
                import_db,
                source_id=source_id,
                resource_type=int(resource_type),
                operator=op_name,
                operator_account=account,
                action="batch_import",
                target_type="resource",
                detail={"task_id": task.task_id, "type": type, "status": "failed", "message": str(e)},
            )
            logger.exception("导入失败: task=%s, source_id=%s, type=%s", task.task_id, source_id, type)
        finally:
            import_db.close()
            try:
                os.unlink(zip_path)
            except OSError:
                pass

    threading.Thread(target=_run_import, daemon=True).start()
    return {"task_id": task.task_id, "message": "导入已开始"}