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
    # 步骤 1：拉取数据
    icons = await external.fetch_icon_list()

    # 步骤 2：保存 JSON 文件
    icon_dir  = os.path.join(settings.FILE_ROOT_DIR, "icon")
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
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        }
        _, is_new = upsert_resource(db, data)
        if is_new:
            added += 1
        else:
            updated += 1

    # 步骤 4：触发向量化
    await external.call_rebuild_icon_api()

    return {"added": added, "updated": updated}
