"""
初始化数据入库服务

读取 FILE_ROOT_DIR/init/ 下的预置文件，批量 UPSERT 到 resources 表。
不触发任何外部 API（无向量化、无拆解）。

目录结构（直接放在 FILE_ROOT_DIR 下）：
  component/
  └── {领域名}/                  ← 子目录名作为 domain fallback
      └── component_index.json  ← { "domain": "...", "componentSets": [...] }
  icon/
  ├── svg.json                   ← [{id, name, englishName, description}]
  └── illustration.json
  template/
  └── templates.json             ← [{name, description, hex_data}]
"""

import hashlib
import json
import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import upsert_resource


# ──────────────────────────────────────────────────────────────────
# 组件集
# ──────────────────────────────────────────────────────────────────

def import_components(db: Session) -> dict:
    """
    扫描 FILE_ROOT_DIR/component/ 的所有子目录。
    每个子目录下寻找 component_index.json 并导入。
    domain 优先取 JSON 文件内的 domain 字段，缺失时以子目录名代替。
    """
    base = os.path.join(settings.FILE_ROOT_DIR, "component")
    if not os.path.isdir(base):
        return {"added": 0, "updated": 0, "error": f"目录不存在：{base}"}

    added = updated = 0
    for entry in sorted(os.scandir(base), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        index_path = os.path.join(entry.path, "component_index.json")
        if not os.path.exists(index_path):
            continue

        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 兼容两种格式：对象格式 / 直接列表格式
        if isinstance(data, list):
            components = data
            domain = entry.name
        else:
            components = data.get("componentSets", [])
            domain = data.get("domain") or entry.name

        for comp in components:
            row = {
                "resource_type": int(ResourceType.component_set),
                "name":          comp.get("name", "未命名组件集"),
                "unique_key":    comp.get("componentKey") or str(uuid.uuid4()),
                "file_path":     comp.get("hexFile"),
                "domain":        domain or None,
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
    """
    读取 init/icon/{icon_type}.json 并导入。
    icon_type: "svg" | "illustration"
    JSON 格式：[{ "id": 1, "name": "...", "englishName": "...", "description": "..." }]
    unique_key = str(id)，与正常同步流程保持一致，可幂等重复导入。
    """
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
            "unique_key":    str(item.get("id", uuid.uuid4())),
            "english_name":  item.get("englishName"),
            "description":   item.get("description"),
            "file_path":     None,
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
    """
    读取 init/template/templates.json 并导入。
    JSON 格式：[{ "name": "...", "description": "...", "hex_data": "..." }]

    unique_key = "init_tmpl_" + md5(name)[:12]
    基于名称生成确定性 key，保证多次导入幂等，不产生重复记录。
    文件路径固定为 template/{unique_key}.txt，覆盖写入。
    """
    file_path = os.path.join(settings.FILE_ROOT_DIR, "template", "templates.json")
    if not os.path.exists(file_path):
        return {"added": 0, "updated": 0, "error": f"文件不存在：{file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    tmpl_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(tmpl_dir, exist_ok=True)

    added = updated = 0
    for item in items:
        name     = item.get("name", "未命名模版")
        hex_data = item.get("hex_data", "")

        # 确定性 unique_key，防止重复导入产生多条记录
        uid = "init_tmpl_" + hashlib.md5(name.encode("utf-8")).hexdigest()[:12]
        rel_path = f"template/{uid}.txt"
        abs_path = os.path.join(settings.FILE_ROOT_DIR, rel_path)

        # 写（或覆盖）hex 文件
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(hex_data)

        row = {
            "resource_type": int(ResourceType.template),
            "name":          name,
            "unique_key":    uid,
            "description":   item.get("description"),
            "file_path":     rel_path,
        }
        _, is_new = upsert_resource(db, row)
        if is_new:
            added += 1
        else:
            updated += 1

    return {"added": added, "updated": updated}


# ──────────────────────────────────────────────────────────────────
# 总入口
# ──────────────────────────────────────────────────────────────────

def run_init_import(db: Session) -> dict:
    """
    按顺序导入所有类型，返回各类型的结果汇总。
    任一类型出错不影响其他类型继续执行。
    """
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
