"""
插画服务
负责：调用插画 API、保存 JSON 文件、写入数据库、入向量库。
"""

import json
import logging
import os

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.clients import external
from app.models.resource import ResourceIllus
from app.services.resource_service import upsert_resource
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)


async def sync_illus(db: Session) -> dict:
    # 步骤 1：拉取数据
    items = await external.fetch_illus_list()

    # 步骤 2：保存 JSON 文件
    save_dir  = os.path.join(settings.FILE_ROOT_DIR, "illus")
    json_path = os.path.join(save_dir, "illus.json")
    os.makedirs(save_dir, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # 步骤 3：写入数据库
    added, updated = 0, 0
    vector_pairs = []

    for item in items:
        illus_id = item.get("id")
        if illus_id is None:
            continue

        alias = item.get("alias", "未命名插画")
        resource_row, is_new = upsert_resource(db, {
            "resource_type": int(ResourceType.illus),
            "name":          alias,
            "description":   item.get("description"),
            "raw_data":      json.dumps(item, ensure_ascii=False),
        })

        _upsert_resource_illus(db, item, resource_row.id)

        if is_new:
            added += 1
        else:
            updated += 1

        vector_pairs.append((resource_row, item))

    # 步骤 4：入向量库
    ingest_vectors(ResourceType.illus, vector_pairs)

    return {"added": added, "updated": updated}


def _upsert_resource_illus(db: Session, item: dict, resource_id: int) -> None:
    illus_id = item.get("id")
    row = db.query(ResourceIllus).filter(ResourceIllus.resource_id == resource_id).first()
    if row is None:
        db.add(ResourceIllus(
            resource_id=resource_id,
            illus_id=illus_id,
            category=item.get("category"),
            tags=item.get("tags"),
            version=item.get("version"),
        ))
    else:
        if illus_id is not None:
            row.illus_id = illus_id
        row.category = item.get("category", row.category)
        row.tags     = item.get("tags",     row.tags)
        row.version  = item.get("version",  row.version)
    db.flush()
