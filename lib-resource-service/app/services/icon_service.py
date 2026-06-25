"""
SVG / 插画服务
负责：调用图标 API、保存 JSON 文件、写入数据库、触发向量化。
"""

import json
import os
from typing import Literal
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.services.resource_service import upsert_resource


async def sync_icons(db: Session, icon_type: Literal["svg", "illustration"]) -> dict:
    """
    同步 SVG 或插画数据：
    1. 调用 ICON_API 获取 JSON 列表
    2. 将 JSON 保存到 FILE_ROOT_DIR/icon/{type}.json
    3. 按 id 做 UPSERT 写入 resources 表
    4. 调用 REBUILD_ICON_API 触发向量化
    返回：{ "added": N, "updated": M }
    """
    # 步骤 1：拉取数据
    icons = await external.fetch_icon_list()

    # 步骤 2：保存 JSON 文件（作为本地备份，也供向量化使用）
    icon_dir = os.path.join(settings.FILE_ROOT_DIR, "icon")
    os.makedirs(icon_dir, exist_ok=True)

    json_path = os.path.join(icon_dir, f"{icon_type}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(icons, f, ensure_ascii=False, indent=2)

    # 步骤 3：写入数据库
    resource_type = int(ResourceType.svg if icon_type == "svg" else ResourceType.illustration)
    added, updated = 0, 0

    for item in icons:
        data = {
            "resource_type": resource_type,
            "name":          item.get("name", ""),
            # 调用方传入的自有 id 作为 unique_key，加类型前缀避免 svg/插画冲突
            "unique_key":    f"{icon_type}-{item.get('id', '')}",
            "english_name":  item.get("englishName"),
            "description":   item.get("description"),
            "file_path":     None,  # SVG/插画无本地文件
        }
        _, is_new = upsert_resource(db, data)
        if is_new:
            added += 1
        else:
            updated += 1

    # 步骤 4：触发向量化
    await external.call_rebuild_icon_api()

    return {"added": added, "updated": updated}
