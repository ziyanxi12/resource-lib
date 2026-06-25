"""
模版服务
负责：将 hex 文本写入文件，并将元数据写入数据库。
"""

import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import upsert_resource


def upload_template(
    db: Session,
    name: str,
    description: Optional[str],
    hex_data: str,
    created_by: Optional[str] = None,
) -> dict:
    """
    上传模版：
    1. 生成 UUID 作为模版唯一 ID
    2. 将 hex 文本写入 FILE_ROOT_DIR/template/{uuid}.txt
    3. 写入 resources 表
    返回写入结果 dict。
    """
    template_id = str(uuid.uuid4())

    # 确保目录存在
    template_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(template_dir, exist_ok=True)

    # 写文件
    file_name     = f"{template_id}.txt"
    abs_path      = os.path.join(template_dir, file_name)
    relative_path = f"template/{file_name}"

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(hex_data)

    file_size = os.path.getsize(abs_path)

    # 写数据库
    data = {
        "resource_type": int(ResourceType.template),
        "name":          name,
        "unique_key":    template_id,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     "text/plain",
        "description":   description,
        "created_by":    created_by,
    }
    resource, _ = upsert_resource(db, data)

    return {
        "id":        resource.id,
        "name":      resource.name,
        "file_path": relative_path,
        "message":   "模版上传成功",
    }
