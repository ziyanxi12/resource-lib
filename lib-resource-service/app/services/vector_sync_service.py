"""
向量精准补录服务

核心功能：
1. 检测数据库存在但向量库缺失的 data_id
2. 反查数据库完整记录并构造向量数据
3. 分批调用向量服务进行补录
4. 基于时间戳的增量向量同步
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource, ComponentVariant, ResourceIcon, ResourceIllus
from app.services import resource_service
from app.services.resource_service import get_all_data_ids
from app.clients import vector_client
from app.services.vector_text_builder import get_registry, ingest_vectors

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# 检测缺失数据
# ──────────────────────────────────────────────────────────────────

def detect_missing_data_ids(
    db: Session,
    resource_type: ResourceType,
    use_check_api: bool = True
) -> dict:
    """
    检测数据库存在但向量库缺失的 data_id
    
    返回：
    {
        "db_count": 4523,
        "vector_count": 4518,
        "missing_count": 5,
        "missing_ids": ["id1", "id2", ...]
    }
    """
    logger.info("检测缺失数据: type=%s", resource_type.name)
    
    db_ids = get_all_data_ids(db, resource_type)
    db_count = len(db_ids)
    logger.info("数据库数量: %d", db_count)
    
    spec = get_registry().get(resource_type)
    if spec is None:
        logger.warning("未找到向量配置: type=%s", resource_type.name)
        return {
            "db_count": db_count,
            "vector_count": 0,
            "missing_count": db_count,
            "missing_ids": db_ids
        }
    
    vec_type = spec.vec_type
    
    if use_check_api:
        try:
            missing_ids = vector_client.check_ids_missing(vec_type, db_ids)
            vector_count = db_count - len(missing_ids)
            logger.info("向量库数量（通过 check API）: %d", vector_count)
        except Exception as e:
            logger.warning("check API 调用失败，fallback 到列表对比: %s", e)
            vec_ids = set(vector_client.get_all_ids(vec_type))
            db_ids_set = set(db_ids)
            missing_ids = list(db_ids_set - vec_ids)
            vector_count = len(vec_ids)
            logger.info("向量库数量（通过列表对比）: %d", vector_count)
    else:
        vec_ids = set(vector_client.get_all_ids(vec_type))
        db_ids_set = set(db_ids)
        missing_ids = list(db_ids_set - vec_ids)
        vector_count = len(vec_ids)
        logger.info("向量库数量（通过列表对比）: %d", vector_count)
    
    missing_count = len(missing_ids)
    logger.info("缺失数量: %d", missing_count)
    
    return {
        "db_count": db_count,
        "vector_count": vector_count,
        "missing_count": missing_count,
        "missing_ids": sorted(missing_ids)
    }


# ──────────────────────────────────────────────────────────────────
# 反查数据库完整记录
# ──────────────────────────────────────────────────────────────────

def query_resources_by_data_ids(
    db: Session,
    resource_type: ResourceType,
    data_ids: List[str]
) -> List[Resource]:
    """
    根据 data_ids 反查数据库完整记录
    """
    if not data_ids:
        logger.info("无缺失 ID，跳过反查")
        return []
    
    logger.info("反查数据库: type=%s ids=%d", resource_type.name, len(data_ids))
    
    if resource_type == ResourceType.component:
        variants = db.query(ComponentVariant).filter(
            ComponentVariant.variant_key.in_(data_ids)
        ).all()
        resource_ids = [v.resource_id for v in variants]
        logger.debug("查到 %d 个 resource_id", len(resource_ids))
        return db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
    
    elif resource_type == ResourceType.icon:
        try:
            icon_ids = [int(did) for did in data_ids]
        except ValueError as e:
            logger.error("icon_id 转换失败: %s", e)
            return []
        icons = db.query(ResourceIcon).filter(
            ResourceIcon.icon_id.in_(icon_ids)
        ).all()
        resource_ids = [i.resource_id for i in icons]
        logger.debug("查到 %d 个 resource_id", len(resource_ids))
        return db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
    
    elif resource_type == ResourceType.illus:
        illus = db.query(ResourceIllus).filter(
            ResourceIllus.illus_id.in_(data_ids)
        ).all()
        resource_ids = [i.resource_id for i in illus]
        logger.debug("查到 %d 个 resource_id", len(resource_ids))
        return db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
    
    else:
        try:
            resource_ids = [int(did) for did in data_ids]
        except ValueError as e:
            logger.error("resource.id 转换失败: %s", e)
            return []
        logger.debug("直接查询 %d 个 resource.id", len(resource_ids))
        return db.query(Resource).filter(Resource.id.in_(resource_ids)).all()


# ──────────────────────────────────────────────────────────────────
# 提取 raw_data 用于构造向量文本
# ──────────────────────────────────────────────────────────────────

def extract_raw_data_from_resource(res: Resource, resource_type: ResourceType) -> dict:
    """
    从 Resource ORM 对象提取 raw_data（用于构造向量文本）
    """
    try:
        raw = json.loads(res.raw_data or "{}")
    except json.JSONDecodeError:
        raw = {}
    
    if resource_type == ResourceType.component:
        cv = res.component_variant
        return {
            "parent_name": raw.get("componentName") or (cv.component_name if cv else "") or "",
            "canvas_name": raw.get("canvasName") or (cv.canvas_name if cv else "") or "",
            "variant_name": raw.get("variantName") or (cv.name if cv else "") or res.name,
            "lib_name": (cv.lib_name if cv else "") or ""
        }
    
    elif resource_type == ResourceType.icon:
        ic = res.icon_detail
        return {
            "chineseName": raw.get("chineseName") or res.name,
            "name": raw.get("name") or (ic.name if ic else "") or "",
            "englishName": raw.get("englishName") or (ic.english_name if ic else "") or "",
            "category": raw.get("category") or (ic.category if ic else "") or "",
            "description": res.description or ""
        }
    
    elif resource_type == ResourceType.illus:
        il = res.illus_detail
        return {
            "id": raw.get("id") or (str(il.illus_id) if il else ""),
            "alias": res.name,
            "description": res.description or "",
            "category": raw.get("category") or (il.category if il else "") or "",
            "tags": raw.get("tags") or (il.tags if il else []) or [],
            "version": raw.get("version") or (il.version if il else "") or ""
        }
    
    else:
        return {
            "name": res.name,
            "description": res.description or ""
        }


# ──────────────────────────────────────────────────────────────────
# 执行精准补录
# ──────────────────────────────────────────────────────────────────

def sync_missing_vectors(
    db: Session,
    resource_type: ResourceType,
    batch_size: int = 200,
    dry_run: bool = False
) -> dict:
    """
    精准补录缺失的向量数据
    
    工作流程：
    1. 检测缺失的 data_ids
    2. 反查数据库完整记录
    3. 构造向量数据并分批入库
    
    返回：
    {
        "detected_missing": 5,
        "actual_synced": 5,
        "batch_count": 1,
        "failed": [],
        "dry_run": false
    }
    """
    logger.info("开始补录: type=%s batch_size=%d dry_run=%s", 
                resource_type.name, batch_size, dry_run)
    
    missing_info = detect_missing_data_ids(db, resource_type)
    missing_ids = missing_info["missing_ids"]
    
    if dry_run:
        logger.info("Dry-run 模式，不实际补录")
        return {
            "detected_missing": len(missing_ids),
            "actual_synced": 0,
            "batch_count": 0,
            "dry_run": True,
            "missing_ids_preview": missing_ids[:10]
        }
    
    if not missing_ids:
        logger.info("无缺失数据，跳过补录")
        return {
            "detected_missing": 0,
            "actual_synced": 0,
            "batch_count": 0,
            "dry_run": False
        }
    
    logger.info("反查数据库记录...")
    resources = query_resources_by_data_ids(db, resource_type, missing_ids)
    
    if not resources:
        logger.warning("反查失败，未找到任何记录")
        return {
            "detected_missing": len(missing_ids),
            "actual_synced": 0,
            "batch_count": 0,
            "failed": missing_ids,
            "dry_run": False
        }
    
    logger.info("查到 %d 条记录", len(resources))
    
    logger.info("构造向量数据...")
    spec = get_registry().get(resource_type)
    vector_pairs = []
    for res in resources:
        raw = extract_raw_data_from_resource(res, resource_type)
        vector_pairs.append((res, raw))
    
    logger.info("开始分批入库...")
    synced_count = 0
    failed_items = []
    total_batches = (len(vector_pairs) + batch_size - 1) // batch_size
    
    for i in range(0, len(vector_pairs), batch_size):
        batch = vector_pairs[i:i+batch_size]
        batch_num = i // batch_size + 1
        logger.info("补录批次 %d/%d: %d 条", batch_num, total_batches, len(batch))
        
        try:
            ingest_vectors(resource_type, batch, skip_vector=False)
            synced_count += len(batch)
            logger.info("批次 %d 成功", batch_num)
        except Exception as e:
            logger.error("批次 %d 失败: %s", batch_num, e)
            failed_items.extend([spec.get_data_id(r) for r, _ in batch])
    
    logger.info("补录完成: 检测=%d 实际=%d 失败=%d",
                len(missing_ids), synced_count, len(failed_items))

    return {
        "detected_missing": len(missing_ids),
        "actual_synced": synced_count,
        "batch_count": total_batches,
        "failed": failed_items,
        "dry_run": False
    }


# ──────────────────────────────────────────────────────────────────
# 全量重建向量库
# ──────────────────────────────────────────────────────────────────

def rebuild_all_vectors(
    db: Session,
    resource_type: ResourceType,
    batch_size: int = 200,
) -> dict:
    """
    从 DB 全量读取记录并入向量库，适用于向量库清空后的完整恢复。
    """
    from sqlalchemy.orm import selectinload

    logger.info("开始全量重建: type=%s", resource_type.name)

    load_opts = [selectinload(Resource.tags)]
    if resource_type == ResourceType.component:
        load_opts.append(selectinload(Resource.component_variant))
    elif resource_type == ResourceType.icon:
        load_opts.append(selectinload(Resource.icon_detail))
    elif resource_type == ResourceType.illus:
        load_opts.append(selectinload(Resource.illus_detail))

    resources = (
        db.query(Resource)
        .options(*load_opts)
        .filter(Resource.resource_type == int(resource_type), Resource.is_deleted == 0)
        .all()
    )

    total = len(resources)
    logger.info("查到 %d 条记录", total)

    if not total:
        return {"total": 0, "synced": 0, "batch_count": 0, "failed": []}

    spec = get_registry().get(resource_type)
    vector_pairs = [
        (res, extract_raw_data_from_resource(res, resource_type))
        for res in resources
    ]

    synced = 0
    failed: List[str] = []
    total_batches = (total + batch_size - 1) // batch_size

    for i in range(0, len(vector_pairs), batch_size):
        batch = vector_pairs[i : i + batch_size]
        batch_num = i // batch_size + 1
        logger.info("重建批次 %d/%d: %d 条", batch_num, total_batches, len(batch))
        try:
            ingest_vectors(resource_type, batch, skip_vector=False)
            synced += len(batch)
        except Exception as e:
            logger.error("批次 %d 失败: %s", batch_num, e)
            if spec:
                failed.extend([spec.get_data_id(r) for r, _ in batch])

    logger.info("全量重建完成: total=%d synced=%d failed=%d", total, synced, len(failed))
    return {
        "total": total,
        "synced": synced,
        "batch_count": total_batches,
        "failed": failed,
    }


# ──────────────────────────────────────────────────────────────────
# 基于时间戳的增量向量同步（新增）
# ──────────────────────────────────────────────────────────────────

_SYNC_BATCH_SIZE = 100


def sync_vectors_by_type(db: Session, resource_type: ResourceType) -> dict:
    """
    同步指定类型的向量数据（基于时间戳）
    
    仅同步 vector_updated_at < updated_at 的数据
    
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

    spec = get_registry().get(resource_type)
    if spec is None:
        logger.warning("未找到资源类型 %s 的向量配置", resource_type)
        return {"total": 0, "synced": 0, "failed": 0, "skipped": 0, "message": "不支持的资源类型"}

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

        items = []
        for res in batch:
            try:
                data_id = spec.get_data_id(res)
                text = spec.build_text(res, {})
                metadata = spec.build_metadata(res, {})
                items.append({
                    "data_id": data_id,
                    "text": text,
                    "metadata": metadata,
                })
                logger.debug("构造向量数据: resource_id=%s, data_id=%s, text=%s", res.id, data_id, text[:100] if text else "")
            except Exception as e:
                logger.warning("构造向量数据失败 resource_id=%s: %s", res.id, e)
                failed_count += 1
                continue

        if not items:
            continue

        try:
            result = vector_client.ingest(spec.vec_type, items)
            
            succeeded = result.get("succeeded", [])
            failed = result.get("failed", [])

            logger.debug("向量入库返回: succeeded=%s, failed=%s", succeeded, failed)

            succeeded_data_ids = set(succeeded) if succeeded else set()
            for res in batch:
                try:
                    res_data_id = spec.get_data_id(res)
                    if res_data_id in succeeded_data_ids:
                        synced_ids.append(res.id)
                        logger.debug("资源同步成功: resource_id=%s, data_id=%s", res.id, res_data_id)
                except Exception:
                    pass
            
            failed_count += len(failed)
            
            logger.info(
                "批次 %d/%d 完成: 成功=%d 失败=%d",
                batch_num, total_batches, len(succeeded), len(failed)
            )

        except Exception as e:
            logger.warning("向量入库异常 type=%s batch=%d: %s", resource_type.name, batch_num, e)
            failed_count += len(batch)

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