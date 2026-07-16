"""
初始化数据入库服务

仅支持组件集初始化，其他资源类型通过 ZIP 上传。

目录结构：
  component/
  └── component_map.json        ← [{fileKey, name, indexPath}]
      └── {任意子目录}/
          └── component_index.json  ← { "domain": "...", "componentSets": [...] }
"""

import json
import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource, ResourceSource
from app.services.resource_service import batch_update_vector_time, build_vector_text
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)


def _get_or_create_default_source(db: Session, resource_type: ResourceType) -> int:
    """获取或创建默认来源，返回 source_id"""
    existing = db.query(ResourceSource).filter(
        ResourceSource.resource_type == int(resource_type)
    ).first()
    if existing:
        return existing.id
    
    source = ResourceSource(
        name=f"手动上传-{resource_type.label}",
        resource_type=int(resource_type),
        is_sync_source=0,
        is_active=1,
    )
    db.add(source)
    db.flush()
    return source.id


def import_components(db: Session, skip_vector: bool = False) -> dict:
    component_map_path = os.path.join(settings.FILE_ROOT_DIR, "component", "component_map.json")
    if not os.path.exists(component_map_path):
        return {"added": 0, "error": "component_map.json 不存在"}

    with open(component_map_path, "r", encoding="utf-8") as f:
        component_map = json.load(f)

    source_id = _get_or_create_default_source(db, ResourceType.component)
    
    all_meta = []
    for entry in component_map:
        index_path = os.path.join(settings.FILE_ROOT_DIR, entry.get("indexPath", ""))
        if not os.path.exists(index_path):
            continue
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        lib_name = entry.get("name")
        components = data if isinstance(data, list) else data.get("componentSets", [])
        
        for comp in components:
            hex_file = comp.get("hexFile")
            file_name = os.path.basename(hex_file) if hex_file else None
            parent_name = comp.get("name", "未命名组件集")
            
            for variant in comp.get("variants", []):
                all_meta.append({
                    "lib_name": lib_name,
                    "parent_name": parent_name,
                    "file_name": file_name,
                    "hex_file": hex_file,
                    "comp": comp,
                    "variant": variant,
                })

    if not all_meta:
        return {"added": 0}

    logger.info("组件集：共 %d 条，开始入库", len(all_meta))

    added = 0
    vector_pairs = []

    for meta in all_meta:
        comp = meta["comp"]
        variant = meta["variant"]
        variant_key = variant.get("variantKey")
        
        file_size = None
        if meta["hex_file"]:
            hex_path = os.path.join(settings.FILE_ROOT_DIR, meta["hex_file"])
            if os.path.exists(hex_path):
                file_size = os.path.getsize(hex_path)
        
        file_name = meta["file_name"]
        file_type = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        resource_data = {
            "resource_type": int(ResourceType.component),
            "source_id": source_id,
            "name": variant.get("name", ""),
            "file_name": file_name,
            "file_path": meta["hex_file"],
            "file_size": file_size,
            "file_type": file_type,
            "data_updated_at": datetime.utcnow(),
            "raw_data": {
                "lib_name": meta["lib_name"],
                "canvas_name": comp.get("canvasName"),
                "component_name": comp.get("name"),
                "component_guid": comp.get("guid"),
                "component_key": comp.get("componentKey"),
                "variant_name": variant.get("name"),
                "variant_guid": variant.get("guid"),
                "variant_key": variant_key,
                "parent_key": variant.get("parentKey"),
                "component_props": variant.get("componentProps", []),
            },
        }
        
        resource = Resource(**resource_data)
        db.add(resource)
        added += 1
        
        vector_pairs.append((resource, {}))

    db.commit()
    logger.info("组件集入库完成：新增 %d 条", added)

    if vector_pairs and not skip_vector:
        for res, _ in vector_pairs:
            res.vector_text = build_vector_text(res)
        db.commit()
        ingest_vectors(ResourceType.component, vector_pairs, skip_vector=False)
        new_ids = [r.id for r, _ in vector_pairs]
        batch_update_vector_time(db, new_ids)

    return {"added": added}


def run_init_import(db: Session, skip_vector: bool = False) -> dict:
    """初始化入库，仅支持组件集"""
    try:
        return {"component": import_components(db, skip_vector=skip_vector)}
    except Exception as e:
        logger.exception("component 入库失败")
        return {"component": {"added": 0, "error": str(e)}}