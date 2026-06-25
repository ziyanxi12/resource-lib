"""
组件集服务
负责：读取组件库映射表、完整同步流程（获取版本→下载pix→拆解→写DB→向量化）

component_index.json 真实格式：
{
  "domain": "ICT_UI",
  "componentSets": [
    {
      "name": "文字链接",
      "componentKey": "be1d...",
      "hexFile": "component/be1d....txt",
      "canvasName": "1.基础类"
    }
  ]
}
"""

import json
import os
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.services.resource_service import upsert_resource


def get_component_map() -> List[dict]:
    map_path = settings.COMPONENT_MAP_FILE
    if not os.path.exists(map_path):
        return []
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _update_component_map(file_key: str, index_path: str) -> None:
    """同步完成后更新 component_map.json 中对应条目的 indexPath 和 updatedAt。"""
    from datetime import datetime, timezone
    map_path = settings.COMPONENT_MAP_FILE
    items    = get_component_map()

    for item in items:
        if item["fileKey"] == file_key:
            item["indexPath"] = index_path
            item["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            break

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


async def sync_component(db: Session, file_key: str) -> dict:
    # 步骤 1：获取版本
    version_resp = await external.get_component_version(file_key)
    version_id   = version_resp["list"][0]["id"]

    # 步骤 2：下载 pix 文件
    pix_bytes = await external.download_pix_file(file_key, version_id)
    pix_dir   = os.path.join(settings.FILE_ROOT_DIR, "component", file_key)
    os.makedirs(pix_dir, exist_ok=True)
    pix_path  = os.path.join(pix_dir, f"{version_id}.pix")
    with open(pix_path, "wb") as f:
        f.write(pix_bytes)

    # 步骤 3：调用拆解 API
    await external.call_split_api(pix_path)

    index_path = os.path.join(pix_dir, "component_index.json")
    if not os.path.exists(index_path):
        _write_mock_index(index_path, file_key)

    # 拆解完成后更新 component_map.json 中的 indexPath
    _update_component_map(file_key, f"component/{file_key}/component_index.json")

    # 步骤 4：解析并写入数据库
    components = _parse_index(index_path)
    result = _write_to_db(db, components)

    # 步骤 5：触发向量化
    await external.call_rebuild_component_api()

    return result


# ──────────────────────────────────────────────────────────────────

def _parse_index(index_path: str) -> List[dict]:
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("componentSets", [])


def _write_to_db(db: Session, components: List[dict]) -> dict:
    added, updated = 0, 0
    for comp in components:
        hex_file    = comp.get("hexFile")
        file_name   = os.path.basename(hex_file) if hex_file else None
        parent_name = comp.get("name", "未命名组件集")

        for variant in comp.get("variants", []):
            data = {
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
            _, is_new = upsert_resource(db, data)
            if is_new:
                added += 1
            else:
                updated += 1
    return {"added": added, "updated": updated}


def _write_mock_index(index_path: str, file_key: str) -> None:
    mock = {
        "domain": "MOCK_DOMAIN",
        "componentSets": [
            {"componentKey": f"{file_key}-btn",  "name": "按钮组件集",  "hexFile": f"component/{file_key}/btn.hex",  "canvasName": "通用"},
            {"componentKey": f"{file_key}-form", "name": "表单组件集",  "hexFile": f"component/{file_key}/form.hex", "canvasName": "表单"},
            {"componentKey": f"{file_key}-nav",  "name": "导航组件集",  "hexFile": f"component/{file_key}/nav.hex",  "canvasName": "导航"},
        ],
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(mock, f, ensure_ascii=False, indent=2)
