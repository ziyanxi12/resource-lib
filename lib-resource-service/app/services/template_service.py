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
from app.services.resource_service import create_resource
from app.services.vector_text_builder import ingest_vectors


def upload_template(
    db: Session,
    name: str,
    description: Optional[str],
    hex_data: str,
    created_by: Optional[str] = None,
) -> dict:
    template_dir = os.path.join(settings.FILE_ROOT_DIR, "template")
    os.makedirs(template_dir, exist_ok=True)

    file_name     = f"{uuid.uuid4()}.txt"
    relative_path = f"template/{file_name}"
    abs_path      = os.path.join(template_dir, file_name)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(hex_data)

    file_size = os.path.getsize(abs_path)

    data = {
        "resource_type": int(ResourceType.template),
        "name":          name,
        "file_name":     file_name,
        "file_path":     relative_path,
        "file_size":     file_size,
        "mime_type":     "text/plain",
        "description":   description,
        "created_by":    created_by,
    }
    resource = create_resource(db, data)
    ingest_vectors(ResourceType.template, [(resource, {"name": name, "description": description or ""})])

    return {
        "id":        resource.id,
        "name":      resource.name,
        "file_path": relative_path,
        "message":   "模版上传成功",
    }
