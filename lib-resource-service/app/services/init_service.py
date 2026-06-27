"""
初始化数据入库服务

读取 FILE_ROOT_DIR/init/ 下的预置文件，批量 UPSERT 到 resources 表及各结构化详情表。
不触发任何外部 API。

目录结构：
  component/
  └── {任意子目录}/
      └── component_index.json  ← { "domain": "...", "componentSets": [...] }
  icon/
  ├── icons.json                ← [{id, name, englishName, category, description}]
  └── illus.json
  template/
  └── templates.json            ← [{name, description, hex_data}]
"""

import json
import logging
import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import ComponentVariant, ResourceIcon
from app.services.resource_service import create_resource, bulk_upsert_resources
from app.services.vector_text_builder import build_component_text, build_icon_text

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# 内部工具：upsert component_variants
# ──────────────────────────────────────────────────────────────────

def _bulk_upsert_component_variants(db: Session, rows: list) -> None:
    """批量 upsert component_variants，优先按 variant_key，其次 guid，最后 resource_id。"""
    if not rows:
        return

    # 按 variant_key 批量预取
    vk_rows    = {r["variant_key"]: r for r in rows if r.get("variant_key")}
    guid_rows  = {r["guid"]: r       for r in rows if not r.get("variant_key") and r.get("guid")}
    rid_rows   = {r["resource_id"]: r for r in rows if not r.get("variant_key") and not r.get("guid")}

    existing_by_vk  = {}
    existing_by_guid = {}
    existing_by_rid  = {}

    if vk_rows:
        for cv in db.query(ComponentVariant).filter(ComponentVariant.variant_key.in_(vk_rows)).all():
            existing_by_vk[cv.variant_key] = cv
    if guid_rows:
        for cv in db.query(ComponentVariant).filter(ComponentVariant.guid.in_(guid_rows)).all():
            existing_by_guid[cv.guid] = cv
    if rid_rows:
        for cv in db.query(ComponentVariant).filter(ComponentVariant.resource_id.in_(rid_rows)).all():
            existing_by_rid[cv.resource_id] = cv

    FIELDS = ["resource_id", "domain", "canvas_name", "component_name",
              "component_guid", "component_key", "name", "component_props"]

    for r in rows:
        existing = (
            existing_by_vk.get(r.get("variant_key"))
            or existing_by_guid.get(r.get("guid"))
            or existing_by_rid.get(r.get("resource_id"))
        )
        if existing:
            for f in FIELDS:
                if r.get(f) is not None:
                    setattr(existing, f, r[f])
        else:
            db.add(ComponentVariant(**r))

    db.flush()


# ──────────────────────────────────────────────────────────────────
# 内部工具：upsert resource_icons
# ──────────────────────────────────────────────────────────────────

def _bulk_upsert_resource_icons(db: Session, rows: list) -> None:
    """批量 upsert resource_icons，按 resource_id 做幂等键。"""
    if not rows:
        return

    resource_ids = [r["resource_id"] for r in rows]
    existing_map = {
        cv.resource_id: cv
        for cv in db.query(ResourceIcon).filter(ResourceIcon.resource_id.in_(resource_ids)).all()
    }

    FIELDS = ["icon_id", "chinese_name", "name", "english_name", "category"]
    for r in rows:
        existing = existing_map.get(r["resource_id"])
        if existing:
            for f in FIELDS:
                if r.get(f) is not None:
                    setattr(existing, f, r[f])
        else:
            db.add(ResourceIcon(**r))

    db.flush()


# ──────────────────────────────────────────────────────────────────
# 组件集
# ──────────────────────────────────────────────────────────────────

def import_components(db: Session, skip_vector: bool = False) -> dict:
    from app.services.component_service import get_component_map
    component_map = get_component_map()
    if not component_map:
        return {"added": 0, "updated": 0, "error": "component_map.json 为空或不存在"}

    # 第1步：遍历所有文件，收集全量数据
    all_resource_data = []
    all_variant_meta  = []  # 与 all_resource_data 一一对应，存 comp/variant/domain

    for entry in component_map:
        index_path = os.path.join(settings.FILE_ROOT_DIR, entry.get("indexPath", ""))
        if not os.path.exists(index_path):
            continue

        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        domain     = data.get("domain") if isinstance(data, dict) else None
        components = data if isinstance(data, list) else data.get("componentSets", [])

        for comp in components:
            hex_file    = comp.get("hexFile")
            file_name   = os.path.basename(hex_file) if hex_file else None
            parent_name = comp.get("name", "未命名组件集")

            for variant in comp.get("variants", []):
                resource_name = variant.get("name", "")
                all_resource_data.append({
                    "resource_type": int(ResourceType.component_set),
                    "name":          resource_name,
                    "file_name":     file_name,
                    "file_path":     hex_file,
                    "mime_type":     "text/plain",
                    "raw_data":      json.dumps({
                        "domain":         domain,
                        "canvasName":     comp.get("canvasName"),
                        "componentKey":   comp.get("componentKey"),
                        "componentGuid":  comp.get("guid"),
                        "componentName":  parent_name,
                        "variantName":    variant.get("name"),
                        "variantKey":     variant.get("variantKey"),
                        "variantGuid":    variant.get("guid"),
                        "parentKey":      variant.get("parentKey"),
                        "componentProps": variant.get("componentProps", []),
                    }, ensure_ascii=False),
                })
                all_variant_meta.append({
                    "comp":          comp,
                    "variant":       variant,
                    "domain":        domain,
                    "resource_name": resource_name,
                    "parent_name":   parent_name,
                })

    if not all_resource_data:
        return {"added": 0, "updated": 0}

    logger.info("组件集：共 %d 条 variant，开始 DB 入库", len(all_resource_data))

    # 第2步：批量 upsert resources（1次 SELECT + add_all + flush）
    resource_map = bulk_upsert_resources(db, all_resource_data, int(ResourceType.component_set))
    added   = sum(1 for _, is_new in resource_map.values() if is_new)
    updated = sum(1 for _, is_new in resource_map.values() if not is_new)
    logger.info("组件集 DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    # 第3步：组装 component_variants 数据
    variant_rows = []
    vector_items = []
    for meta in all_variant_meta:
        comp        = meta["comp"]
        variant     = meta["variant"]
        domain      = meta["domain"]
        parent_name = meta["parent_name"]
        name        = meta["resource_name"]

        resource_row, _ = resource_map.get(name, (None, None))
        if resource_row is None:
            continue

        variant_rows.append({
            "resource_id":     resource_row.id,
            "domain":          domain,
            "canvas_name":     comp.get("canvasName"),
            "component_name":  comp.get("name"),
            "component_guid":  comp.get("guid"),
            "component_key":   variant.get("parentKey") or comp.get("componentKey"),
            "name":            variant.get("name", ""),
            "guid":            variant.get("guid"),
            "variant_key":     variant.get("variantKey"),
            "component_props": variant.get("componentProps"),
        })
        vector_items.append({
            "data_id": str(resource_row.id),
            "text": build_component_text(
                parent_name,
                comp.get("canvasName", ""),
                variant.get("name", ""),
            ),
            "metadata": {
                "name":           resource_row.name,
                "canvas_name":    comp.get("canvasName", ""),
                "component_name": parent_name,
                "domain":         domain or "",
            },
        })

    # 第4步：批量 upsert component_variants（最多3次 SELECT + add_all + flush）
    _bulk_upsert_component_variants(db, variant_rows)

    # 第5步：统一提交
    db.commit()
    logger.info("组件集：DB 全部提交完成")

    if not skip_vector and settings.VECTOR_SERVICE_ENABLED and vector_items:
        logger.info("组件集：开始向量入库，共 %d 条", len(vector_items))
        try:
            from app.clients import vector_client
            result = vector_client.ingest("component", vector_items)
            logger.info("组件向量入库完成：成功 %d 条，失败 %d 条", len(result["succeeded"]), len(result["failed"]))
        except Exception as e:
            logger.warning("组件向量入库异常（不影响 DB 结果）: %s", e)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# SVG / 插画
# ──────────────────────────────────────────────────────────────────

def import_icons(db: Session, icon_type: str, skip_vector: bool = False) -> dict:
    if icon_type == "svg":
        file_path = os.path.join(settings.FILE_ROOT_DIR, "icon", "icons.json")
    else:
        file_path = os.path.join(settings.FILE_ROOT_DIR, "illus", "illus.json")
    if not os.path.exists(file_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    resource_type = int(
        ResourceType.svg if icon_type == "svg" else ResourceType.illustration
    )

    # 第1步：收集全量 resource 数据
    all_resource_data = []
    for item in items:
        chinese_name = item.get("chineseName") or item.get("name", "未命名")
        all_resource_data.append({
            "resource_type": resource_type,
            "name":          chinese_name,
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        })

    logger.info("%s：共 %d 条，开始 DB 入库", icon_type, len(all_resource_data))

    # 第2步：批量 upsert resources
    resource_map = bulk_upsert_resources(db, all_resource_data, resource_type)
    added   = sum(1 for _, is_new in resource_map.values() if is_new)
    updated = sum(1 for _, is_new in resource_map.values() if not is_new)
    logger.info("%s DB 入库完成：新增 %d 条，更新 %d 条", icon_type, added, updated)

    # 第3步：组装 icon 详情数据
    icon_rows    = []
    vector_items = []
    for item in items:
        chinese_name = item.get("chineseName") or item.get("name", "未命名")
        resource_row, _ = resource_map.get(chinese_name, (None, None))
        if resource_row is None:
            continue

        icon_rows.append({
            "resource_id":  resource_row.id,
            "icon_id":      item.get("id"),
            "chinese_name": item.get("chineseName"),
            "name":         item.get("name"),
            "english_name": item.get("englishName"),
            "category":     item.get("category"),
        })

        if icon_type == "svg":
            vector_items.append({
                "data_id": str(resource_row.id),
                "text": build_icon_text(
                    item.get("category", ""),
                    chinese_name,
                    item.get("name", ""),
                    item.get("englishName", ""),
                    item.get("description", ""),
                ),
                "metadata": {
                    "name":         resource_row.name,
                    "description":  item.get("description", ""),
                    "english_name": item.get("englishName", ""),
                    "category":     item.get("category", ""),
                },
            })

    # 第4步：批量 upsert resource_icons
    _bulk_upsert_resource_icons(db, icon_rows)

    # 第5步：统一提交
    db.commit()
    logger.info("%s：DB 全部提交完成", icon_type)

    if not skip_vector and settings.VECTOR_SERVICE_ENABLED and vector_items:
        logger.info("%s：开始向量入库，共 %d 条", icon_type, len(vector_items))
        try:
            from app.clients import vector_client
            result = vector_client.ingest("icon", vector_items)
            logger.info("图标向量入库完成：成功 %d 条，失败 %d 条", len(result["succeeded"]), len(result["failed"]))
        except Exception as e:
            logger.warning("图标向量入库异常（不影响 DB 结果）: %s", e)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# 模版
# ──────────────────────────────────────────────────────────────────

def import_templates(db: Session) -> dict:
    json_path = os.path.join(settings.FILE_ROOT_DIR, "template", "templates.json")
    if not os.path.exists(json_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{json_path}"}

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    tmpl_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(tmpl_dir, exist_ok=True)

    added = 0
    for item in items:
        name     = item.get("name", "未命名模版")
        hex_data = item.get("hex_data", "")

        file_name = f"{uuid.uuid4()}.txt"
        rel_path  = f"template/{file_name}"
        abs_path  = os.path.join(settings.FILE_ROOT_DIR, rel_path)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(hex_data)

        create_resource(db, {
            "resource_type": int(ResourceType.template),
            "name":          name,
            "file_name":     file_name,
            "file_path":     rel_path,
            "description":   item.get("description"),
        })
        added += 1

    return {"added": added, "updated": 0}


# ──────────────────────────────────────────────────────────────────
# 总入口
# ──────────────────────────────────────────────────────────────────

def run_init_import(db: Session, skip_vector: bool = False) -> dict:
    results = {}

    try:
        results["component"] = import_components(db, skip_vector=skip_vector)
    except Exception as e:
        results["component"] = {"added": 0, "updated": 0, "error": str(e)}

    for icon_type in ("svg", "illustration"):
        try:
            results[icon_type] = import_icons(db, icon_type, skip_vector=skip_vector)
        except Exception as e:
            results[icon_type] = {"added": 0, "updated": 0, "error": str(e)}

    try:
        results["template"] = import_templates(db)
    except Exception as e:
        results["template"] = {"added": 0, "updated": 0, "error": str(e)}

    return results
