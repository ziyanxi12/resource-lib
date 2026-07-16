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


def sync_vectors_by_type(db: Session, resource_type: ResourceType) -> dict:
    """
    同步指定类型的向量数据（基于时间戳）
    
    仅同步 vector_updated_at < data_updated_at 的数据
    
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

    resources, total = resource_service.get_resources_need_sync(db, int(resource_type))
    
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