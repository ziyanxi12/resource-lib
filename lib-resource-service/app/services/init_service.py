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
from app.models.resource import ComponentVariant, Resource, ResourceIcon
from app.services.resource_service import create_resource
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
    seen_ids: set = set()
    for r in rows:
        rid = r["resource_id"]
        existing = existing_map.get(rid)
        if existing:
            for f in FIELDS:
                if r.get(f) is not None:
                    setattr(existing, f, r[f])
            seen_ids.add(rid)
        elif rid not in seen_ids:
            db.add(ResourceIcon(**r))
            seen_ids.add(rid)

    db.flush()


# ──────────────────────────────────────────────────────────────────
# 组件集
# ──────────────────────────────────────────────────────────────────

def import_components(db: Session, skip_vector: bool = False) -> dict:
    from app.services.component_service import get_component_map
    component_map = get_component_map()
    if not component_map:
        return {"added": 0, "updated": 0, "error": "component_map.json 为空或不存在"}

    # 第1步：遍历所有文件，收集全量 meta
    all_meta = []
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
                all_meta.append({
                    "comp":        comp,
                    "variant":     variant,
                    "domain":      domain,
                    "parent_name": parent_name,
                    "file_name":   file_name,
                    "hex_file":    hex_file,
                })

    if not all_meta:
        return {"added": 0, "updated": 0}

    logger.info("组件集：共 %d 条 variant，开始 DB 入库", len(all_meta))

    # 第2步：按 variant_key 批量查已有 component_variants → resource_id
    all_variant_keys = [
        m["variant"].get("variantKey") for m in all_meta if m["variant"].get("variantKey")
    ]
    existing_cv_map = {}  # variant_key → ComponentVariant
    if all_variant_keys:
        for cv in db.query(ComponentVariant).filter(
            ComponentVariant.variant_key.in_(all_variant_keys)
        ).all():
            existing_cv_map[cv.variant_key] = cv

    existing_resource_map = {}  # resource_id → Resource
    existing_rids = {cv.resource_id for cv in existing_cv_map.values()}
    if existing_rids:
        for r in db.query(Resource).filter(Resource.id.in_(existing_rids)).all():
            existing_resource_map[r.id] = r

    # 第3步：逐条 upsert resource，暂存 resource 对象引用
    added = 0
    updated = 0
    variant_rows  = []
    vector_metas  = []

    for meta in all_meta:
        comp        = meta["comp"]
        variant     = meta["variant"]
        domain      = meta["domain"]
        parent_name = meta["parent_name"]
        variant_key = variant.get("variantKey")

        resource_data = {
            "resource_type": int(ResourceType.component_set),
            "name":      variant.get("name", ""),
            "file_name": meta["file_name"],
            "file_path": meta["hex_file"],
            "mime_type": "text/plain",
            "raw_data":  json.dumps({
                "domain":         domain,
                "canvasName":     comp.get("canvasName"),
                "componentKey":   comp.get("componentKey"),
                "componentGuid":  comp.get("guid"),
                "componentName":  parent_name,
                "variantName":    variant.get("name"),
                "variantKey":     variant_key,
                "variantGuid":    variant.get("guid"),
                "parentKey":      variant.get("parentKey"),
                "componentProps": variant.get("componentProps", []),
            }, ensure_ascii=False),
        }

        existing_cv = existing_cv_map.get(variant_key) if variant_key else None
        if existing_cv:
            resource_row = existing_resource_map.get(existing_cv.resource_id)
            if resource_row is None:
                resource_row = Resource(**resource_data)
                db.add(resource_row)
            else:
                for k, v in resource_data.items():
                    if hasattr(resource_row, k) and v is not None:
                        setattr(resource_row, k, v)
            updated += 1
        else:
            resource_row = Resource(**resource_data)
            db.add(resource_row)
            added += 1

        variant_rows.append({
            "_res":          resource_row,
            "domain":          domain,
            "canvas_name":     comp.get("canvasName"),
            "component_name":  comp.get("name"),
            "component_guid":  comp.get("guid"),
            "component_key":   variant.get("parentKey") or comp.get("componentKey"),
            "name":            variant.get("name", ""),
            "guid":            variant.get("guid"),
            "variant_key":     variant_key,
            "component_props": variant.get("componentProps"),
        })
        vector_metas.append({
            "_res":        resource_row,
            "parent_name": parent_name,
            "canvas_name": comp.get("canvasName", ""),
            "variant_name": variant.get("name", ""),
            "domain":      domain or "",
        })

    # 第4步：flush 使新增 resource 拿到 id
    db.flush()
    logger.info("组件集 DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    # 第5步：填充 resource_id，批量 upsert component_variants
    for row in variant_rows:
        row["resource_id"] = row.pop("_res").id
    _bulk_upsert_component_variants(db, variant_rows)

    # 第6步：统一提交
    db.commit()
    logger.info("组件集：DB 全部提交完成")

    if not skip_vector and settings.VECTOR_SERVICE_ENABLED and vector_metas:
        logger.info("组件集：开始向量入库，共 %d 条", len(vector_metas))
        try:
            from app.clients import vector_client
            vector_items = [
                {
                    "data_id": str(m["_res"].id),
                    "text": build_component_text(m["parent_name"], m["canvas_name"], m["variant_name"]),
                    "metadata": {
                        "name":           m["_res"].name,
                        "canvas_name":    m["canvas_name"],
                        "component_name": m["parent_name"],
                        "domain":         m["domain"],
                    },
                }
                for m in vector_metas
            ]
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

    logger.info("%s：共 %d 条，开始 DB 入库", icon_type, len(items))

    # 第1步：按 icon_id 批量预取已有记录，构建 icon_id → (ResourceIcon, Resource) 映射
    all_icon_ids = [item["id"] for item in items if item.get("id") is not None]
    existing_icon_map: dict = {}  # icon_id → ResourceIcon
    if all_icon_ids:
        for ri in db.query(ResourceIcon).filter(ResourceIcon.icon_id.in_(all_icon_ids)).all():
            existing_icon_map[ri.icon_id] = ri

    existing_resource_map: dict = {}  # resource_id → Resource
    existing_rids = {ri.resource_id for ri in existing_icon_map.values()}
    if existing_rids:
        for r in db.query(Resource).filter(Resource.id.in_(existing_rids)).all():
            existing_resource_map[r.id] = r

    # 第2步：逐条 upsert resource + resource_icons
    added = 0
    updated = 0
    icon_rows    = []
    vector_items = []

    for item in items:
        icon_id = item.get("id")
        if icon_id is None:
            logger.warning("图标缺少 id 字段，跳过：%s", item)
            continue
        chinese_name = item.get("chineseName") or item.get("name", "未命名")
        resource_data = {
            "resource_type": resource_type,
            "name":          chinese_name,
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        }

        existing_ri = existing_icon_map.get(icon_id)
        if existing_ri:
            resource_row = existing_resource_map.get(existing_ri.resource_id)
            if resource_row is None:
                resource_row = Resource(**resource_data)
                db.add(resource_row)
            else:
                for k, v in resource_data.items():
                    if hasattr(resource_row, k) and v is not None:
                        setattr(resource_row, k, v)
            updated += 1
        else:
            resource_row = Resource(**resource_data)
            db.add(resource_row)
            added += 1

        icon_rows.append({
            "_res":         resource_row,
            "_existing_ri": existing_ri,
            "icon_id":      icon_id,
            "chinese_name": item.get("chineseName"),
            "name":         item.get("name"),
            "english_name": item.get("englishName"),
            "category":     item.get("category"),
        })

        if icon_type == "svg":
            vector_items.append({
                "_res": resource_row,
                "item": item,
                "chinese_name": chinese_name,
            })

    # 第3步：flush 使新增 resource 拿到 id
    db.flush()
    logger.info("%s DB 入库完成：新增 %d 条，更新 %d 条", icon_type, added, updated)

    # 第4步：upsert resource_icons
    ICON_FIELDS = ["icon_id", "chinese_name", "name", "english_name", "category"]
    for row in icon_rows:
        existing_ri = row.pop("_existing_ri")
        resource_id = row.pop("_res").id
        if existing_ri:
            for f in ICON_FIELDS:
                if row.get(f) is not None:
                    setattr(existing_ri, f, row[f])
        else:
            db.add(ResourceIcon(resource_id=resource_id, **{f: row.get(f) for f in ICON_FIELDS}))

    # 第5步：统一提交
    db.commit()
    logger.info("%s：DB 全部提交完成", icon_type)

    if not skip_vector and settings.VECTOR_SERVICE_ENABLED and vector_items:
        logger.info("%s：开始向量入库，共 %d 条", icon_type, len(vector_items))
        try:
            from app.clients import vector_client
            ingest_items = [
                {
                    "data_id": str(m["_res"].id),
                    "text": build_icon_text(
                        m["item"].get("category", ""),
                        m["chinese_name"],
                        m["item"].get("name", ""),
                        m["item"].get("englishName", ""),
                        m["item"].get("description", ""),
                    ),
                    "metadata": {
                        "name":         m["_res"].name,
                        "description":  m["item"].get("description", ""),
                        "english_name": m["item"].get("englishName", ""),
                        "category":     m["item"].get("category", ""),
                    },
                }
                for m in vector_items
            ]
            result = vector_client.ingest("icon", ingest_items)
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
