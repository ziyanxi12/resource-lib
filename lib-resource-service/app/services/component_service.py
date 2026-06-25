"""
组件集服务
负责：读取组件库映射表、完整同步流程（获取版本→下载pix→拆解→写DB→向量化）

component_index.json 真实格式：
{
  "domain": "ICT_UI",          ← resources.domain 使用此字段
  "componentSets": [
    {
      "name": "文字链接",
      "componentKey": "be1d...",
      "hexFile": "component/be1d....txt",
      "canvasName": "1.基础类"  ← 画布分类，不作为领域存储
    }
  ]
}
"""

import json
import os
import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.services.resource_service import upsert_resource


def get_component_map() -> List[dict]:
    """
    读取 component_map.json，返回可选组件库列表。
    格式：[{ "fileKey": "abc123", "name": "基础组件库" }]
    """
    map_path = settings.COMPONENT_MAP_FILE
    if not os.path.exists(map_path):
        return []
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def sync_component(db: Session, file_key: str) -> dict:
    """
    完整同步流程：
    1. GET_VERSION_API → 取最新版本 ID（list[0].id）
    2. GET_FILE_API    → 下载 pix 文件，暂存本地
    3. SPLIT_API       → 拆解 pix，生成 hex 文件 + component_index.json
    4. 解析 component_index.json → UPSERT resources 表
    5. REBUILD_COMPONENT_API → 触发向量化

    Mock 模式下步骤 1-3 返回模拟数据，步骤 3 后生成占位 component_index.json，
    其余步骤与生产模式完全相同。
    """
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

    # 步骤 3：调用拆解 API（生产模式会在 pix_dir 生成 component_index.json）
    await external.call_split_api(pix_path)

    # Mock 模式下 split 不真正生成文件，此处补充生成占位 index
    index_path = os.path.join(pix_dir, "component_index.json")
    if not os.path.exists(index_path):
        _write_mock_index(index_path, file_key)

    # 步骤 4：解析 component_index.json 并写入数据库
    components, domain = _parse_index(index_path)
    result = _write_to_db(db, components, domain)

    # 步骤 5：触发向量化
    await external.call_rebuild_component_api()

    return result


# ──────────────────────────────────────────────────────────────────
# 私有辅助函数
# ──────────────────────────────────────────────────────────────────

def _parse_index(index_path: str) -> Tuple[List[dict], str]:
    """
    解析 component_index.json，返回 (componentSets列表, 顶层domain)。

    支持两种格式：
      真实格式：{ "domain": "ICT_UI", "componentSets": [...] }
      旧格式：  直接是 list（domain 返回空串）
    """
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data, ""

    return data.get("componentSets", []), data.get("domain", "")


def _write_to_db(db: Session, components: List[dict], domain: str) -> dict:
    """
    批量 UPSERT 组件集到 resources 表。

    字段映射：
      name         → name
      componentKey → unique_key
      hexFile      → file_path
      domain（顶层）→ domain（所有组件共享同一个领域值，如 "ICT_UI"）
      canvasName   → 不存储（画布分类，与领域无关）
    """
    added, updated = 0, 0
    for comp in components:
        data = {
            "resource_type": int(ResourceType.component_set),
            "name":       comp.get("name", "未命名组件集"),
            "unique_key": comp.get("componentKey") or str(uuid.uuid4()),
            "file_path":  comp.get("hexFile"),
            "domain":     domain or None,
        }
        _, is_new = upsert_resource(db, data)
        if is_new:
            added += 1
        else:
            updated += 1
    return {"added": added, "updated": updated}


def _write_mock_index(index_path: str, file_key: str) -> None:
    """
    Mock 模式下生成占位 component_index.json。
    格式与真实文件保持一致，方便切换时无缝对接。
    """
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
