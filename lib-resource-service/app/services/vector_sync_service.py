"""
向量精准补录服务

核心功能：
1. 检测数据库存在但向量库缺失的资源
2. 反查数据库完整记录并构造向量数据
3. 分批调用向量服务进行补录
4. 基于时间戳的增量向量同步
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource
from app.services import resource_service
from app.clients import vector_client
from app.services.vector_text_builder import ingest_vectors
from app.services.resource_service import build_vector_text

logger = logging.getLogger(__name__)


def detect_missing_resources(
    db: Session,
    resource_type: ResourceType,
) -> dict:
    """
    检测数据库存在但向量库缺失的资源
    
    返回：
    {
        "db_count": 4523,
        "vector_count": 4518,
        "missing_count": 5,
        "missing_ids": [1, 2, ...]
    }
    """
    logger.info("检测缺失数据: type=%s", resource_type.name)
    
    from app.enums import ResourceType as RT
    vec_type_map = {
        RT.component: "component",
        RT.template: "template",
        RT.icon: "icon",
        RT.illus: "illustration",
        RT.image: "image",
        RT.file: "file",
    }
    
    vec_type = vec_type_map.get(resource_type)
    if vec_type is None:
        logger.warning("未找到向量配置: type=%s", resource_type.name)
        return {
            "db_count": 0,
            "vector_count": 0,
            "missing_count": 0,
            "missing_ids": []
        }
    
    resources = db.query(Resource).filter(
        Resource.resource_type == int(resource_type),
        Resource.is_deleted == 0
    ).all()
    
    db_ids = [str(r.id) for r in resources]
    db_count = len(db_ids)
    logger.info("数据库数量: %d", db_count)
    
    try:
        missing_ids = vector_client.check_ids_missing(vec_type, db_ids)
        vector_count = db_count - len(missing_ids)
        logger.info("向量库数量: %d", vector_count)
    except Exception as e:
        logger.warning("check API 调用失败，fallback 到列表对比: %s", e)
        vec_ids = set(vector_client.get_all_ids(vec_type))
        db_ids_set = set(db_ids)
        missing_ids = list(db_ids_set - vec_ids)
        vector_count = len(vec_ids)
        logger.info("向量库数量: %d", vector_count)
    
    missing_count = len(missing_ids)
    logger.info("缺失数量: %d", missing_count)
    
    return {
        "db_count": db_count,
        "vector_count": vector_count,
        "missing_count": missing_count,
        "missing_ids": sorted([int(i) for i in missing_ids])
    }


_SYNC_BATCH_SIZE = 100


def sync_vectors_by_type(db: Session, resource_type: ResourceType, source_id: int = None) -> dict:
    """
    同步指定类型的向量数据（基于时间戳）
    
    仅同步 vector_updated_at < data_updated_at 的数据
    
    参数：
        db: 数据库会话
        resource_type: 资源类型
        source_id: 来源ID（可选，用于筛选）
    
    返回：
    {
        "total": 待同步总数,
        "synced": 成功同步数,
        "failed": 失败数,
        "skipped": 跳过数,
        "message": "同步完成：成功 X 条，失败 Y 条"
    }
    """
    if not settings.VECTOR_SERVICE_ENABLED:
        logger.info("向量服务未启用，跳过同步")
        return {"total": 0, "synced": 0, "failed": 0, "skipped": 0, "message": "向量服务未启用"}

    resources, total = resource_service.get_resources_need_sync(db, int(resource_type), source_id)
    
    if not resources:
        logger.info("类型 %s 无待同步数据", resource_type.name)
        return {"total": 0, "synced": 0, "failed": 0, "skipped": 0, "message": "无待同步数据"}

    logger.info("开始同步类型 %s: 共 %d 条待同步", resource_type.name, total)

    synced_ids: List[int] = []
    failed_count = 0

    for i in range(0, len(resources), _SYNC_BATCH_SIZE):
        batch = resources[i:i + _SYNC_BATCH_SIZE]
        batch_num = i // _SYNC_BATCH_SIZE + 1
        total_batches = (len(resources) + _SYNC_BATCH_SIZE - 1) // _SYNC_BATCH_SIZE
        
        logger.info(
            "同步批次 %d/%d: type=%s 本批=%d条",
            batch_num, total_batches, resource_type.name, len(batch)
        )

        vector_pairs = []
        for res in batch:
            res.vector_text = build_vector_text(res)
            vector_pairs.append((res, {}))
        
        db.flush()

        try:
            ingest_vectors(resource_type, vector_pairs, skip_vector=False)
            synced_ids.extend([r.id for r in batch])
            logger.info("批次 %d 成功", batch_num)
        except Exception as e:
            logger.warning("向量入库异常 type=%s batch=%d: %s", resource_type.name, batch_num, e)
            failed_count += len(batch)

    db.commit()
    
    if synced_ids:
        updated = resource_service.batch_update_vector_time(db, synced_ids)
        logger.info("更新向量同步时间: %d 条", updated)

    logger.info(
        "同步完成 type=%s: 总计=%d 成功=%d 失败=%d",
        resource_type.name, total, len(synced_ids), failed_count
    )

    return {
        "total": total,
        "synced": len(synced_ids),
        "failed": failed_count,
        "skipped": 0,
        "message": f"同步完成：成功 {len(synced_ids)} 条，失败 {failed_count} 条"
    }


_VEC_TYPE_MAP = {
    ResourceType.component: "component",
    ResourceType.template: "template",
    ResourceType.icon: "icon",
    ResourceType.illus: "illustration",
    ResourceType.image: "image",
    ResourceType.file: "file",
}


def rebuild_all_vectors_by_type(
    db: Session,
    resource_type: ResourceType,
    source_id: int = None,
) -> dict:
    """
    全量重建向量库：忽略时间戳，重新 ingest 所有数据 + 清理孤儿数据。

    步骤1: 查 DB 所有未删除资源，逐批 build_vector_text → ingest_vectors
    步骤2: 获取向量库所有 data_id，删除 DB 中不存在的孤儿数据
    步骤3: 返回汇总

    参数：
        db: 数据库会话
        resource_type: 资源类型
        source_id: 来源ID（可选，用于筛选）

    返回：
        {
            "total": DB 数据量,
            "synced": re-ingest 成功数,
            "failed": re-ingest 失败数,
            "orphans_deleted": 清理孤儿数,
            "message": "全量重建完成：成功 X 条，失败 Y 条，清理孤儿 Z 条"
        }
    """
    if not settings.VECTOR_SERVICE_ENABLED:
        logger.info("向量服务未启用，跳过全量重建")
        return {"total": 0, "synced": 0, "failed": 0, "orphans_deleted": 0, "message": "向量服务未启用"}

    vec_type = _VEC_TYPE_MAP.get(resource_type)
    if vec_type is None:
        return {"total": 0, "synced": 0, "failed": 0, "orphans_deleted": 0, "message": f"未找到向量配置: type={resource_type.name}"}

    # ===== 步骤1: 全量 re-ingest =====
    query = db.query(Resource).filter(
        Resource.resource_type == int(resource_type),
        Resource.is_deleted == 0,
    )
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)
    resources = query.order_by(Resource.id).all()
    total = len(resources)

    logger.info("全量重建开始: type=%s  共 %d 条", resource_type.name, total)

    if not resources:
        logger.info("类型 %s 无数据", resource_type.name)
    else:
        synced_ids: List[int] = []
        failed_count = 0

        for i in range(0, len(resources), _SYNC_BATCH_SIZE):
            batch = resources[i:i + _SYNC_BATCH_SIZE]
            batch_num = i // _SYNC_BATCH_SIZE + 1
            total_batches = (len(resources) + _SYNC_BATCH_SIZE - 1) // _SYNC_BATCH_SIZE

            logger.info(
                "全量重建批次 %d/%d: type=%s 本批=%d条",
                batch_num, total_batches, resource_type.name, len(batch),
            )

            vector_pairs = []
            for res in batch:
                res.vector_text = build_vector_text(res)
                vector_pairs.append((res, {}))

            db.flush()

            try:
                ingest_vectors(resource_type, vector_pairs, skip_vector=False)
                synced_ids.extend([r.id for r in batch])
                logger.info("批次 %d 成功", batch_num)
            except Exception as e:
                logger.warning("向量入库异常 type=%s batch=%d: %s", resource_type.name, batch_num, e)
                failed_count += len(batch)

        db.commit()

        if synced_ids:
            resource_service.batch_update_vector_time(db, synced_ids)
            logger.info("更新向量同步时间: %d 条", len(synced_ids))

        logger.info(
            "全量重建 re-ingest 完成 type=%s: 总计=%d 成功=%d 失败=%d",
            resource_type.name, total, len(synced_ids), failed_count,
        )

    # ===== 步骤2: 清理孤儿数据 =====
    orphans_deleted = 0
    try:
        db_ids = set(str(r.id) for r in resources)
        vec_ids = set(vector_client.get_all_ids(vec_type))
        orphan_ids = list(vec_ids - db_ids)

        if orphan_ids:
            logger.info("发现孤儿数据: type=%s 共 %d 条: %s", resource_type.name, len(orphan_ids), orphan_ids[:20])
            result = vector_client.batch_delete(vec_type, orphan_ids)
            orphans_deleted = result.get("total_deleted", 0)
            logger.info("孤儿清理完成: type=%s 删除 %d 条", resource_type.name, orphans_deleted)
        else:
            logger.info("无孤儿数据: type=%s", resource_type.name)
    except Exception as e:
        logger.warning("孤儿清理异常 type=%s: %s", resource_type.name, e)

    # ===== 步骤3: 返回汇总 =====
    synced_count = len(resources) - failed_count if resources else 0
    message = f"全量重建完成：成功 {synced_count} 条，失败 {failed_count if resources else 0} 条，清理孤儿 {orphans_deleted} 条"
    logger.info(message)

    return {
        "total": total,
        "synced": synced_count,
        "failed": failed_count if resources else 0,
        "orphans_deleted": orphans_deleted,
        "message": message,
    }