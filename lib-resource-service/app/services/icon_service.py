"""
SVG 图标服务
负责：调用图标 API、保存 JSON 文件、写入数据库、入向量库。
"""

import json
import logging
import os

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.models.resource import ResourceIcon
from app.services.resource_service import upsert_resource
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)


async def sync_icons(db: Session) -> dict:
    # 步骤 1：拉取数据
    icons = await external.fetch_icon_list()

    # 步骤 2：保存 JSON 文件
    save_dir  = os.path.join(settings.FILE_ROOT_DIR, "icon")
    json_path = os.path.join(save_dir, "icons.json")
    os.makedirs(save_dir, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(icons, f, ensure_ascii=False, indent=2)

    # 步骤 3：写入数据库
    added, updated = 0, 0
    vector_pairs = []

    for item in icons:
        chinese_name = item.get("chineseName") or item.get("name", "未命名")
        resource_row, is_new = upsert_resource(db, {
            "resource_type": int(ResourceType.icon),
            "name":          chinese_name,
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        })

        _upsert_resource_icon(db, item, resource_row.id)

        if is_new:
            added += 1
        else:
            updated += 1

        vector_pairs.append((resource_row, item))

    # 步骤 4：入向量库
    ingest_vectors(ResourceType.icon, vector_pairs)

    return {"added": added, "updated": updated}


def _upsert_resource_icon(db: Session, item: dict, resource_id: int) -> None:
    icon_id = item.get("id")
    row = db.query(ResourceIcon).filter(ResourceIcon.resource_id == resource_id).first()
    if row is None:
        db.add(ResourceIcon(
            resource_id=resource_id,
            icon_id=icon_id,
            chinese_name=item.get("chineseName"),
            name=item.get("name"),
            english_name=item.get("englishName"),
            category=item.get("category"),
        ))
    else:
        row.icon_id      = icon_id if icon_id is not None else row.icon_id
        row.chinese_name = item.get("chineseName", row.chinese_name)
        row.name         = item.get("name", row.name)
        row.english_name = item.get("englishName", row.english_name)
        row.category     = item.get("category", row.category)
    db.flush()
