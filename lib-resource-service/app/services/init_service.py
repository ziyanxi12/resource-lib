"""
初始化数据入库服务

读取 FILE_ROOT_DIR/init/ 下的预置文件，批量 UPSERT 到 resources 表。
不触发任何外部 API（无向量化、无拆解）。

目录结构：
  component/
  └── {任意子目录}/
      └── component_index.json  ← { "domain": "...", "componentSets": [...] }
  icon/
  ├── svg.json                   ← [{id, name, description}]
  └── illustration.json
  template/
  └── templates.json             ← [{name, description, hex_data}]
"""

import json
import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import upsert_resource, create_resource


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
                row = {
                    "resource_type": int(ResourceType.component_set),
                    "name":          f"{parent_name} / {variant.get('name', '')}",
                    "file_name":     file_name,
                    "file_path":     hex_file,
                    "mime_type":     "text/plain",
                    "raw_data":      json.dumps({
                        "variantKey":     variant.get("variantKey"),
                        "parentKey":      variant.get("parentKey"),
                        "parentName":     parent_name,
                        "guid":           variant.get("guid"),
                        "componentProps": variant.get("componentProps", []),
                    }, ensure_ascii=False),
                }
                _, is_new = upsert_resource(db, row)
                if is_new:
                    added += 1
                else:
                    updated += 1

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# SVG / 插画
# ──────────────────────────────────────────────────────────────────

def import_icons(db: Session, icon_type: str) -> dict:
    file_path = os.path.join(settings.FILE_ROOT_DIR, "icon", f"{icon_type}.json")
    if not os.path.exists(file_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    resource_type = int(
        ResourceType.svg if icon_type == "svg" else ResourceType.illustration
    )
    added = updated = 0
    for item in items:
        row = {
            "resource_type": resource_type,
            "name":          item.get("name", "未命名"),
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        }
        _, is_new = upsert_resource(db, row)
        if is_new:
            added += 1
        else:
            updated += 1

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

        row = {
            "resource_type": int(ResourceType.template),
            "name":          name,
            "file_name":     file_name,
            "file_path":     rel_path,
            "description":   item.get("description"),
        }
        create_resource(db, row)
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
