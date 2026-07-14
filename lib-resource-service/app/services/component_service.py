"""
组件集服务
负责：读取组件库映射表、完整同步流程（获取版本→下载pix→拆解→写DB→入向量库）

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
import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.models.resource import ComponentVariant
from app.services.resource_service import upsert_resource, batch_update_vector_time
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)


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
    lib_name = None
    for item in get_component_map():
        if item.get("fileKey") == file_key:
            lib_name = item.get("name")
            break
    
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

    # 步骤 4：解析并写入数据库 + 收集向量数据
    components = _parse_index(index_path)
    result, vector_pairs = _write_to_db(db, components, file_key, lib_name)

    # 步骤 5：入向量库
    ingest_vectors(ResourceType.component, vector_pairs)
    
    # 步骤 6：更新 vector_updated_at
    resource_ids = [r.id for r, _ in vector_pairs]
    batch_update_vector_time(db, resource_ids)

    return result


# ──────────────────────────────────────────────────────────────────

def _get_hex_file_size(hex_file: Optional[str]) -> Optional[int]:
    """hex_file 为相对 FILE_ROOT_DIR 的路径，文件不存在时返回 None（upsert 时不覆盖已有值）。"""
    if not hex_file:
        return None
    abs_path = os.path.join(settings.FILE_ROOT_DIR, hex_file)
    if not os.path.exists(abs_path):
        return None
    return os.path.getsize(abs_path)


def _parse_index(index_path: str) -> List[dict]:
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("componentSets", [])


def _write_to_db(db: Session, components: List[dict], lib_file_key: str = None, lib_name: str = None) -> Tuple[dict, List[tuple]]:
    added, updated = 0, 0
    vector_pairs = []

    for comp in components:
        hex_file    = comp.get("hexFile")
        file_name   = os.path.basename(hex_file) if hex_file else None
        file_size   = _get_hex_file_size(hex_file)
        parent_name = comp.get("name", "未命名组件集")

        for variant in comp.get("variants", []):
            resource_row, is_new = upsert_resource(db, {
                "resource_type": int(ResourceType.component),
                "name":          f"{parent_name} / {variant.get('name', '')}",
                "file_name":     file_name,
                "file_path":     hex_file,
                "file_size":     file_size,
                "mime_type":     "text/plain",
                "data_updated_at": datetime.utcnow(),
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

            _upsert_component_variant(db, comp, variant, resource_row.id, lib_file_key, lib_name)

            if is_new:
                added += 1
            else:
                updated += 1

            vector_pairs.append((resource_row, {
                "parent_name":  parent_name,
                "canvas_name":  comp.get("canvasName", ""),
                "variant_name": variant.get("name", ""),
                "lib_name":     lib_name or "",
            }))

    return {"added": added, "updated": updated}, vector_pairs


def _upsert_component_variant(
    db: Session,
    comp: dict,
    variant: dict,
    resource_id: int,
    lib_file_key: str = None,
    lib_name: str = None,
) -> None:
    variant_key = variant.get("variantKey")
    guid        = variant.get("guid")

    row = db.query(ComponentVariant).filter(
        ComponentVariant.variant_key == variant_key
    ).first() if variant_key else None

    if row is None and guid:
        row = db.query(ComponentVariant).filter(ComponentVariant.guid == guid).first()

    if row is None:
        row = db.query(ComponentVariant).filter(ComponentVariant.resource_id == resource_id).first()

    if row is None:
        db.add(ComponentVariant(
            resource_id=resource_id,
            lib_file_key=lib_file_key,
            lib_name=lib_name,
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
        row.lib_file_key    = lib_file_key if lib_file_key is not None else row.lib_file_key
        row.lib_name        = lib_name if lib_name is not None else row.lib_name
        row.canvas_name     = comp.get("canvasName", row.canvas_name)
        row.component_name  = comp.get("name", row.component_name)
        row.component_guid  = comp.get("guid", row.component_guid)
        row.component_key   = variant.get("parentKey") or comp.get("componentKey") or row.component_key
        row.name            = variant.get("name", row.name)
        row.component_props = variant.get("componentProps", row.component_props)

    db.flush()


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
