"""
SVG / 插画服务
负责：调用图标 API、保存 JSON 文件、写入数据库、入向量库（仅 SVG）。
"""

import json
import logging
import os
from typing import Literal

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.models.resource import ResourceIcon
from app.services.resource_service import upsert_resource
from app.services.vector_text_builder import build_icon_text

logger = logging.getLogger(__name__)


async def sync_icons(db: Session, icon_type: Literal["svg", "illustration"]) -> dict:
    # 步骤 1：拉取数据
    icons = await external.fetch_icon_list()

    # 步骤 2：保存 JSON 文件
    if icon_type == "svg":
        save_dir  = os.path.join(settings.FILE_ROOT_DIR, "icon")
        json_path = os.path.join(save_dir, "icons.json")
    else:
        save_dir  = os.path.join(settings.FILE_ROOT_DIR, "illus")
        json_path = os.path.join(save_dir, "illus.json")
    os.makedirs(save_dir, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(icons, f, ensure_ascii=False, indent=2)

    # 步骤 3：写入数据库
    resource_type = int(ResourceType.svg if icon_type == "svg" else ResourceType.illustration)
    added, updated = 0, 0
    vector_items = []

    for item in icons:
        resource_row, is_new = upsert_resource(db, {
            "resource_type": resource_type,
            "name":          item.get("name", ""),
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        })

        _upsert_resource_icon(db, item, resource_row.id)

        if is_new:
            added += 1
        else:
            updated += 1

        if icon_type == "svg":
            vector_items.append({
                "data_id": str(resource_row.id),
                "text": build_icon_text(
                    item.get("name", ""),
                    item.get("englishName", ""),
                    item.get("description", ""),
                    item.get("category", ""),
                ),
                "metadata": {
                    "name": resource_row.name,
                    "description": item.get("description", ""),
                    "english_name": item.get("englishName", ""),
                    "category": item.get("category", ""),
                },
            })

    # 步骤 4：入向量库（仅 SVG）
    if settings.VECTOR_SERVICE_ENABLED and vector_items:
        try:
            from app.clients import vector_client
            vector_client.ingest("icon", vector_items)
            logger.info("图标向量入库完成：%d 条", len(vector_items))
        except Exception as e:
            logger.warning("图标向量入库异常（不影响 DB 结果）: %s", e)

    return {"added": added, "updated": updated}


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
        row.category     = item.get("category", row.category)
    db.flush()
