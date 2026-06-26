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
import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import ComponentVariant, ResourceIcon
from app.services.resource_service import upsert_resource, create_resource


# ──────────────────────────────────────────────────────────────────
# 内部工具：upsert component_variants
# ──────────────────────────────────────────────────────────────────

def _upsert_component_variant(
    db: Session,
    comp: dict,
    variant: dict,
    resource_id: int,
) -> None:
    """以 variant_key 为幂等键，upsert 一条 ComponentVariant 记录。"""
    variant_key = variant.get("variantKey")
    guid = variant.get("guid")

    row = db.query(ComponentVariant).filter(
        ComponentVariant.variant_key == variant_key
    ).first() if variant_key else None

    if row is None and guid:
        row = db.query(ComponentVariant).filter(ComponentVariant.guid == guid).first()

    if row is None:
        db.add(ComponentVariant(
            resource_id=resource_id,
            canvas_name=comp.get("canvasName"),
            component_name=comp.get("name"),
            component_guid=comp.get("guid"),
            component_key=variant.get("parentKey") or comp.get("componentKey"),
            name=variant.get("name", ""),
            guid=guid,
            variant_key=variant_key,
            component_props=variant.get("componentProps"),
        ))
    else:
        row.resource_id     = resource_id
        row.canvas_name     = comp.get("canvasName", row.canvas_name)
        row.component_name  = comp.get("name", row.component_name)
        row.component_guid  = comp.get("guid", row.component_guid)
        row.component_key   = variant.get("parentKey") or comp.get("componentKey") or row.component_key
        row.name            = variant.get("name", row.name)
        row.component_props = variant.get("componentProps", row.component_props)

    db.flush()


# ──────────────────────────────────────────────────────────────────
# 内部工具：upsert resource_icons
# ──────────────────────────────────────────────────────────────────

def _upsert_resource_icon(db: Session, item: dict, resource_id: int) -> None:
    row = db.query(ResourceIcon).filter(ResourceIcon.resource_id == resource_id).first()
    if row is None:
        db.add(ResourceIcon(
            resource_id=resource_id,
            english_name=item.get("englishName"),
            category=item.get("category"),
        ))
    else:
        row.english_name = item.get("englishName", row.english_name)
        row.category = item.get("category", row.category)
    db.flush()


# ──────────────────────────────────────────────────────────────────
# 组件集
# ──────────────────────────────────────────────────────────────────

def import_components(db: Session) -> dict:
    from app.services.component_service import get_component_map
    component_map = get_component_map()
    if not component_map:
        return {"added": 0, "updated": 0, "error": "component_map.json 为空或不存在"}

    added = updated = 0
    for entry in component_map:
        index_path = os.path.join(settings.FILE_ROOT_DIR, entry.get("indexPath", ""))
        if not os.path.exists(index_path):
            continue

        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        components = data if isinstance(data, list) else data.get("componentSets", [])

        for comp in components:
            hex_file    = comp.get("hexFile")
            file_name   = os.path.basename(hex_file) if hex_file else None
            parent_name = comp.get("name", "未命名组件集")

            for variant in comp.get("variants", []):
                # 写 resources 主表
                resource_row, is_new = upsert_resource(db, {
                    "resource_type": int(ResourceType.component_set),
                    "name":          f"{parent_name} / {variant.get('name', '')}",
                    "file_name":     file_name,
                    "file_path":     hex_file,
                    "mime_type":     "text/plain",
                    "raw_data":      json.dumps({
                        "canvasName":      comp.get("canvasName"),
                        "componentKey":    comp.get("componentKey"),
                        "componentGuid":   comp.get("guid"),
                        "componentName":   parent_name,
                        "variantName":     variant.get("name"),
                        "variantKey":      variant.get("variantKey"),
                        "variantGuid":     variant.get("guid"),
                        "parentKey":       variant.get("parentKey"),
                        "componentProps":  variant.get("componentProps", []),
                    }, ensure_ascii=False),
                })

                # 写 component_variants 详情表
                _upsert_component_variant(db, comp, variant, resource_row.id)

                if is_new:
                    added += 1
                else:
                    updated += 1

    db.commit()
    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# SVG / 插画
# ──────────────────────────────────────────────────────────────────

def import_icons(db: Session, icon_type: str) -> dict:
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
    added = updated = 0
    for item in items:
        # 写 resources 主表
        resource_row, is_new = upsert_resource(db, {
            "resource_type": resource_type,
            "name":          item.get("name", "未命名"),
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        })

        # 写 resource_icons 详情表
        _upsert_resource_icon(db, item, resource_row.id)

        if is_new:
            added += 1
        else:
            updated += 1

    db.commit()
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

def run_init_import(db: Session) -> dict:
    results = {}

    try:
        results["component"] = import_components(db)
    except Exception as e:
        results["component"] = {"added": 0, "updated": 0, "error": str(e)}

    for icon_type in ("svg", "illustration"):
        try:
            results[icon_type] = import_icons(db, icon_type)
        except Exception as e:
            results[icon_type] = {"added": 0, "updated": 0, "error": str(e)}

    try:
        results["template"] = import_templates(db)
    except Exception as e:
        results["template"] = {"added": 0, "updated": 0, "error": str(e)}

    return results
