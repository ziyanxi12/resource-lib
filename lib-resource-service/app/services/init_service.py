"""
初始化数据入库服务

读取 FILE_ROOT_DIR 下的预置文件，批量 UPSERT 到 resources 表及各结构化详情表。
不触发任何外部 API。

目录结构：
  component/
  └── {任意子目录}/
      └── component_index.json  ← { "domain": "...", "componentSets": [...] }
  icon/
  └── icons.json                ← [{id, name, chineseName, englishName, category, description}]
  illus/
  └── illus.json                ← [{id, alias, description, category, tags, version}]
  template/
  └── templates.json            ← [{name, file_name, description}]
  image/
  └── images.json              ← [{name, file_name, description}]
"""

import json
import logging
import os
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import ComponentVariant, Resource, ResourceIcon, ResourceIllus
from app.services.resource_service import create_resource
from app.services.vector_text_builder import ingest_vectors

try:
    from PIL import Image as PILImage
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# 内部工具：upsert component_variants
# ──────────────────────────────────────────────────────────────────

def _bulk_upsert_component_variants(db: Session, rows: list) -> None:
    """批量 upsert component_variants，按 variant_key（PK）查找，无则新增。"""
    if not rows:
        return

    valid_rows = {r["variant_key"]: r for r in rows if r.get("variant_key")}
    if not valid_rows:
        return

    existing = {
        cv.variant_key: cv
        for cv in db.query(ComponentVariant).filter(
            ComponentVariant.variant_key.in_(valid_rows)
        ).all()
    }

    UPDATE_FIELDS = ["resource_id", "domain", "canvas_name", "component_name",
                     "component_guid", "component_key", "name", "guid", "component_props"]

    for vk, r in valid_rows.items():
        cv = existing.get(vk)
        if cv:
            for f in UPDATE_FIELDS:
                if r.get(f) is not None:
                    setattr(cv, f, r[f])
        else:
            db.add(ComponentVariant(**r))

    db.flush()


# ──────────────────────────────────────────────────────────────────
# 组件集
# ──────────────────────────────────────────────────────────────────

def import_components(db: Session, skip_vector: bool = False) -> dict:
    from app.services.component_service import get_component_map
    component_map = get_component_map()
    if not component_map:
        return {"added": 0, "updated": 0, "error": "component_map.json 为空或不存在"}

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
        standalone = data.get("standaloneComponents", []) if isinstance(data, dict) else []
        for comp in standalone:
            component_key = comp.get("componentKey")
            hex_file      = comp.get("hexFile")
            all_meta.append({
                "comp":        comp,
                "variant": {
                    "name":           comp.get("name", ""),
                    "guid":           comp.get("guid"),
                    "variantKey":     component_key,
                    "parentKey":      component_key,
                    "componentProps": comp.get("componentProps", []),
                },
                "domain":      domain,
                "parent_name": comp.get("name", "未命名组件"),
                "file_name":   os.path.basename(hex_file) if hex_file else None,
                "hex_file":    hex_file,
            })

    if not all_meta:
        return {"added": 0, "updated": 0}

    logger.info("组件集：共 %d 条 variant，开始 DB 入库", len(all_meta))

    all_variant_keys = [
        m["variant"].get("variantKey") for m in all_meta if m["variant"].get("variantKey")
    ]
    existing_cv_map = {}
    if all_variant_keys:
        for cv in db.query(ComponentVariant).filter(
            ComponentVariant.variant_key.in_(all_variant_keys)
        ).all():
            existing_cv_map[cv.variant_key] = cv

    existing_resource_map = {}
    existing_rids = {cv.resource_id for cv in existing_cv_map.values()}
    if existing_rids:
        for r in db.query(Resource).filter(Resource.id.in_(existing_rids)).all():
            existing_resource_map[r.id] = r

    added = 0
    updated = 0
    variant_rows = []
    vector_pairs = []

    for meta in all_meta:
        comp        = meta["comp"]
        variant     = meta["variant"]
        domain      = meta["domain"]
        parent_name = meta["parent_name"]
        variant_key = variant.get("variantKey")

        resource_data = {
            "resource_type": int(ResourceType.component),
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
            updated += 1
            continue  # 已入库的数据跳过，不重复更新也不重复入向量

        resource_row = Resource(**resource_data)
        db.add(resource_row)
        added += 1

        variant_rows.append({
            "_res":           resource_row,
            "domain":         domain,
            "canvas_name":    comp.get("canvasName"),
            "component_name": comp.get("name"),
            "component_guid": comp.get("guid"),
            "component_key":  variant.get("parentKey") or comp.get("componentKey"),
            "name":           variant.get("name", ""),
            "guid":           variant.get("guid"),
            "variant_key":    variant_key,
            "component_props": variant.get("componentProps"),
        })
        vector_pairs.append((resource_row, {
            "parent_name":  parent_name,
            "canvas_name":  comp.get("canvasName", ""),
            "variant_name": variant.get("name", ""),
            "domain":       domain or "",
        }))

    db.flush()
    logger.info("组件集 DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    for row in variant_rows:
        row["resource_id"] = row.pop("_res").id
    _bulk_upsert_component_variants(db, variant_rows)

    db.commit()
    logger.info("组件集：DB 全部提交完成")

    ingest_vectors(ResourceType.component, vector_pairs, skip_vector=skip_vector)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# SVG 图标
# ──────────────────────────────────────────────────────────────────

def import_icons(db: Session, skip_vector: bool = False) -> dict:
    file_path = os.path.join(settings.FILE_ROOT_DIR, "icon", "icons.json")
    if not os.path.exists(file_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    logger.info("icon：共 %d 条，开始 DB 入库", len(items))

    all_icon_ids = [item["id"] for item in items if item.get("id") is not None]
    existing_icon_map: dict = {}
    if all_icon_ids:
        for ri in db.query(ResourceIcon).filter(ResourceIcon.icon_id.in_(all_icon_ids)).all():
            existing_icon_map[ri.icon_id] = ri

    existing_resource_map: dict = {}
    existing_rids = {ri.resource_id for ri in existing_icon_map.values()}
    if existing_rids:
        for r in db.query(Resource).filter(Resource.id.in_(existing_rids)).all():
            existing_resource_map[r.id] = r

    added = 0
    updated = 0
    icon_rows    = []
    vector_pairs = []

    for item in items:
        icon_id = item.get("id")
        if icon_id is None:
            logger.warning("图标缺少 id 字段，跳过：%s", item)
            continue
        chinese_name = item.get("chineseName") or item.get("name", "未命名")
        resource_data = {
            "resource_type": int(ResourceType.icon),
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
            "group":        item.get("group"),
        })
        vector_pairs.append((resource_row, item))

    db.flush()
    logger.info("icon DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    ICON_INSERT_FIELDS  = ["icon_id", "chinese_name", "name", "english_name", "category", "group"]
    ICON_UPDATE_FIELDS  = ["chinese_name", "name", "english_name", "category", "group"]
    for row in icon_rows:
        existing_ri = row.pop("_existing_ri")
        resource_id = row.pop("_res").id
        if existing_ri:
            for f in ICON_UPDATE_FIELDS:
                if row.get(f) is not None:
                    setattr(existing_ri, f, row[f])
        else:
            db.add(ResourceIcon(resource_id=resource_id, **{f: row.get(f) for f in ICON_INSERT_FIELDS}))

    db.commit()
    logger.info("icon：DB 全部提交完成")

    ingest_vectors(ResourceType.icon, vector_pairs, skip_vector=skip_vector)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# 插画
# ──────────────────────────────────────────────────────────────────

def import_illus(db: Session, skip_vector: bool = False) -> dict:
    file_path = os.path.join(settings.FILE_ROOT_DIR, "illus", "illus.json")
    if not os.path.exists(file_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    logger.info("illus：共 %d 条，开始 DB 入库", len(items))

    all_illus_ids = [item["id"] for item in items if item.get("id") is not None]
    existing_illus_map: dict = {}
    if all_illus_ids:
        for ri in db.query(ResourceIllus).filter(ResourceIllus.illus_id.in_(all_illus_ids)).all():
            existing_illus_map[ri.illus_id] = ri

    existing_resource_map: dict = {}
    existing_rids = {ri.resource_id for ri in existing_illus_map.values()}
    if existing_rids:
        for r in db.query(Resource).filter(Resource.id.in_(existing_rids)).all():
            existing_resource_map[r.id] = r

    added = 0
    updated = 0
    illus_rows   = []
    vector_pairs = []

    for item in items:
        illus_id = item.get("id")
        if illus_id is None:
            logger.warning("插画缺少 id 字段，跳过：%s", item)
            continue
        resource_data = {
            "resource_type": int(ResourceType.illus),
            "name":          item.get("alias", "未命名插画"),
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        }

        existing_ri = existing_illus_map.get(illus_id)
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

        raw_tags = item.get("tags")
        if isinstance(raw_tags, list):
            tags_list = raw_tags
        elif isinstance(raw_tags, str) and raw_tags.strip():
            tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
        else:
            tags_list = []

        illus_rows.append({
            "_res":         resource_row,
            "_existing_ri": existing_ri,
            "illus_id":     illus_id,
            "category":     item.get("category"),
            "tags":         tags_list,
            "version":      item.get("version"),
        })
        vector_pairs.append((resource_row, item))

    db.flush()
    logger.info("illus DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    ILLUS_INSERT_FIELDS = ["illus_id", "category", "tags", "version"]
    ILLUS_UPDATE_FIELDS = ["category", "tags", "version"]
    for row in illus_rows:
        existing_ri = row.pop("_existing_ri")
        resource_id = row.pop("_res").id
        if existing_ri:
            for f in ILLUS_UPDATE_FIELDS:
                if row.get(f) is not None:
                    setattr(existing_ri, f, row[f])
        else:
            db.add(ResourceIllus(resource_id=resource_id, **{f: row.get(f) for f in ILLUS_INSERT_FIELDS}))

    db.commit()
    logger.info("illus：DB 全部提交完成")

    ingest_vectors(ResourceType.illus, vector_pairs, skip_vector=skip_vector)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# 模版
# ──────────────────────────────────────────────────────────────────

def import_templates(db: Session, skip_vector: bool = False) -> dict:
    json_path = os.path.join(settings.FILE_ROOT_DIR, "template", "templates.json")
    if not os.path.exists(json_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{json_path}"}

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    logger.info("template：共 %d 条，开始 DB 入库", len(items))

    all_names = [item.get("name") for item in items if item.get("name")]
    existing_map = {}
    if all_names:
        for r in db.query(Resource).filter(
            Resource.resource_type == int(ResourceType.template),
            Resource.name.in_(all_names)
        ).all():
            existing_map[r.name] = r

    added = 0
    updated = 0
    vector_pairs = []

    for item in items:
        name = item.get("name")
        if not name:
            logger.warning("模版缺少 name 字段，跳过：%s", item)
            continue

        rel_path = item.get("file_name")
        if not rel_path:
            logger.warning("模版缺少 file_name 字段，跳过：%s", item)
            continue

        abs_path = os.path.join(settings.FILE_ROOT_DIR, rel_path)
        if not os.path.exists(abs_path):
            logger.warning("模版文件不存在，跳过：%s", abs_path)
            continue

        file_name = os.path.basename(rel_path)
        file_size = os.path.getsize(abs_path)

        resource_data = {
            "resource_type": int(ResourceType.template),
            "name":          name,
            "file_name":     file_name,
            "file_path":     rel_path,
            "file_size":     file_size,
            "mime_type":     "text/plain",
            "description":   item.get("description"),
        }

        existing = existing_map.get(name)
        if existing:
            for k, v in resource_data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            resource_row = existing
            updated += 1
        else:
            resource_row = Resource(**resource_data)
            db.add(resource_row)
            added += 1

        vector_pairs.append((resource_row, item))

    db.flush()
    db.commit()
    logger.info("template DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    ingest_vectors(ResourceType.template, vector_pairs, skip_vector=skip_vector)

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# 总入口
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 图片
# ──────────────────────────────────────────────────────────────────

def import_images(db: Session, skip_vector: bool = False) -> dict:
    json_path = os.path.join(settings.FILE_ROOT_DIR, "image", "images.json")
    if not os.path.exists(json_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{json_path}"}

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    logger.info("image：共 %d 条，开始 DB 入库", len(items))

    all_names = [item.get("name") for item in items if item.get("name")]
    existing_map = {}
    if all_names:
        for r in db.query(Resource).filter(
            Resource.resource_type == int(ResourceType.image),
            Resource.name.in_(all_names)
        ).all():
            existing_map[r.name] = r

    added = 0
    updated = 0
    vector_pairs = []

    for item in items:
        name = item.get("name")
        if not name:
            logger.warning("图片缺少 name 字段，跳过：%s", item)
            continue

        rel_path = item.get("file_name")
        if not rel_path:
            logger.warning("图片缺少 file_name 字段，跳过：%s", item)
            continue

        abs_path = os.path.join(settings.FILE_ROOT_DIR, rel_path)
        if not os.path.exists(abs_path):
            logger.warning("图片文件不存在，跳过：%s", abs_path)
            continue

        file_name = os.path.basename(rel_path)
        file_size = os.path.getsize(abs_path)
        mime_type = _get_mime_type(file_name)
        dimensions = _extract_dimensions_from_file(abs_path)

        resource_data = {
            "resource_type": int(ResourceType.image),
            "name":          name,
            "file_name":     file_name,
            "file_path":     rel_path,
            "file_size":     file_size,
            "mime_type":     mime_type,
            "dimensions":    dimensions,
            "description":   item.get("description"),
        }

        existing = existing_map.get(name)
        if existing:
            for k, v in resource_data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            resource_row = existing
            updated += 1
        else:
            resource_row = Resource(**resource_data)
            db.add(resource_row)
            added += 1

        vector_pairs.append((resource_row, item))

    db.flush()
    db.commit()
    logger.info("image DB 入库完成：新增 %d 条，更新 %d 条", added, updated)

    ingest_vectors(ResourceType.image, vector_pairs, skip_vector=skip_vector)

    return {"added": added, "updated": updated}


def _get_mime_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {
        "png":  "image/png",
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "svg":  "image/svg+xml",
        "gif":  "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/octet-stream")


def _extract_dimensions_from_file(abs_path: str) -> Optional[dict]:
    if not _HAS_PILLOW:
        return None
    try:
        img = PILImage.open(abs_path)
        return {"width": img.width, "height": img.height}
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────
# 总入口
# ──────────────────────────────────────────────────────────────────

def run_init_import(db: Session, skip_vector: bool = False) -> dict:
    results = {}

    for name, fn in [
        ("component", lambda: import_components(db, skip_vector=skip_vector)),
        ("icon",      lambda: import_icons(db, skip_vector=skip_vector)),
        ("illus",     lambda: import_illus(db, skip_vector=skip_vector)),
        ("template",  lambda: import_templates(db, skip_vector=skip_vector)),
        ("image",     lambda: import_images(db, skip_vector=skip_vector)),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"added": 0, "updated": 0, "error": str(e)}

    return results
