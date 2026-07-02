"""
向量精准补录服务

核心功能：
1. 检测数据库存在但向量库缺失的 data_id
2. 反查数据库完整记录并构造向量数据
3. 分批调用向量服务进行补录
"""

import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.enums import ResourceType
from app.models.resource import Resource, ComponentVariant, ResourceIcon, ResourceIllus
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
    
    # 1. 从数据库获取所有 data_id
    db_ids = get_all_data_ids(db, resource_type)
    db_count = len(db_ids)
    logger.info("数据库数量: %d", db_count)
    
    # 2. 从向量库获取缺失列表
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
    
    # 方式A：使用 check API（推荐，性能好）
    if use_check_api:
        try:
            missing_ids = vector_client.check_ids_missing(vec_type, db_ids)
            vector_count = db_count - len(missing_ids)
            logger.info("向量库数量（通过 check API）: %d", vector_count)
        except Exception as e:
            logger.warning("check API 调用失败，fallback 到列表对比: %s", e)
            # Fallback 到方式B
            vec_ids = set(vector_client.get_all_ids(vec_type))
            db_ids_set = set(db_ids)
            missing_ids = list(db_ids_set - vec_ids)
            vector_count = len(vec_ids)
            logger.info("向量库数量（通过列表对比）: %d", vector_count)
    else:
        # 方式B：对比两个列表（如果向量服务未实现 check API）
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
    
    不同类型的查询策略：
    - component: 通过 ComponentVariant.variant_key 反查
    - icon: 通过 ResourceIcon.icon_id 反查（转为 int）
    - illus: 通过 ResourceIllus.illus_id 反查
    - template/image: 通过 Resource.id 反查（转为 int）
    """
    if not data_ids:
        logger.info("无缺失 ID，跳过反查")
        return []
    
    logger.info("反查数据库: type=%s ids=%d", resource_type.name, len(data_ids))
    
    if resource_type == ResourceType.component:
        # 先查 component_variants 表获取 resource_id
        variants = db.query(ComponentVariant).filter(
            ComponentVariant.variant_key.in_(data_ids)
        ).all()
        resource_ids = [v.resource_id for v in variants]
        logger.debug("查到 %d 个 resource_id", len(resource_ids))
        return db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
    
    elif resource_type == ResourceType.icon:
        # icon_id 需转为 int
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
    
    else:  # template, image
        # resource.id 需转为 int
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
    
    不同类型的提取策略：
    - component: 从 component_variant + raw_data 提取
    - icon: 从 icon_detail + raw_data 提取
    - illus: 从 illus_detail + raw_data 提取
    - template/image: 从 Resource 基础字段提取
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
            "variant_name": res.name,
            "domain": raw.get("domain") or (cv.domain if cv else "") or ""
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
    
    else:  # template, image
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
    
    # 1. 检测缺失
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
    
    # 2. 反查数据库完整记录
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
    
    # 3. 构造向量数据
    logger.info("构造向量数据...")
    spec = get_registry().get(resource_type)
    vector_pairs = []
    for res in resources:
        raw = extract_raw_data_from_resource(res, resource_type)
        vector_pairs.append((res, raw))
    
    # 4. 分批入库
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