import csv
import io
import json
import logging
import os
import zipfile
from typing import Generator, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.services.resource_service import get_resources

logger = logging.getLogger(__name__)

EXPORT_LIMIT = 5000


def get_export_resources(
    db: Session,
    resource_type: Optional[int] = None,
    source_id: Optional[int] = None,
    search: Optional[str] = None,
    group_id: Optional[int] = None,
) -> Tuple[List, bool]:
    items, total = get_resources(
        db,
        resource_type=resource_type,
        source_id=source_id,
        search=search,
        page=1,
        limit=EXPORT_LIMIT + 1,
        group_id=group_id,
    )
    truncated = len(items) > EXPORT_LIMIT
    if truncated:
        items = items[:EXPORT_LIMIT]
    return items, truncated


def _fmt_export(r, display_map=None) -> dict:
    def _display(val):
        if not val:
            return val
        if display_map:
            return display_map.get(val, val)
        return val
    return {
        "id": r.id,
        "resource_type": r.resource_type,
        "resource_type_name": ResourceType(r.resource_type).name,
        "source_id": r.source_id,
        "source_name": r.source.name if r.source else None,
        "name": r.name,
        "description": r.description,
        "ai_description": r.ai_description,
        "search_text": r.search_text,
        "vector_text": r.vector_text,
        "file_name": r.file_name,
        "file_path": r.file_path,
        "file_size": r.file_size,
        "file_type": r.file_type,
        "width": r.width,
        "height": r.height,
        "thumbnail_path": r.thumbnail_path,
        "raw_data": r.raw_data,
        "group_id": r.group_id,
        "group_path": r.group.real_path if r.group else None,
        "created_by": _display(r.created_by),
        "updated_by": _display(r.updated_by),
        "created_at": int(r.created_at.timestamp() * 1000) if r.created_at else None,
        "updated_at": int(r.updated_at.timestamp() * 1000) if r.updated_at else None,
        "data_updated_at": int(r.data_updated_at.timestamp() * 1000) if r.data_updated_at else None,
        "vector_updated_at": int(r.vector_updated_at.timestamp() * 1000) if r.vector_updated_at else None,
        "tags": r.tags or [],
    }


def _resolve_display_map(db: Session, resources: List) -> dict:
    from app.services.user_service import resolve_display_names
    accounts = set()
    for r in resources:
        if r.created_by:
            accounts.add(r.created_by)
        if r.updated_by:
            accounts.add(r.updated_by)
    return resolve_display_names(db, list(accounts))


def serialize_resources(db: Session, resources: List) -> Tuple[List[dict], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """在 session 关闭前预序列化所有资源为纯 dict，同时收集文件路径。

    Returns:
        - items: 序列化后的 dict 列表
        - file_entries: [(abs_path, arcname), ...]  资源文件
        - thumb_entries: [(abs_path, arcname), ...]  缩略图
    """
    display_map = _resolve_display_map(db, resources)
    items = []
    file_entries = []
    thumb_entries = []

    for r in resources:
        item = _fmt_export(r, display_map)
        items.append(item)

        if r.file_path:
            abs_path = os.path.join(settings.FILE_ROOT_DIR, r.file_path)
            if os.path.isfile(abs_path):
                file_entries.append((abs_path, f"data/{r.file_path}"))
            else:
                logger.warning("导出 ZIP 跳过缺失文件: resource_id=%s, file_path=%s", r.id, r.file_path)

        if r.thumbnail_path:
            thumb_abs = os.path.join(settings.FILE_ROOT_DIR, r.thumbnail_path)
            if os.path.isfile(thumb_abs):
                thumb_entries.append((thumb_abs, f"image/{r.thumbnail_path}"))
            else:
                logger.warning("导出 ZIP 跳过缺失缩略图: resource_id=%s, thumbnail_path=%s", r.id, r.thumbnail_path)

    return items, file_entries, thumb_entries


def export_json_stream(items: List[dict]) -> Generator[bytes, None, None]:
    yield b"["
    for i, item in enumerate(items):
        chunk = json.dumps(item, ensure_ascii=False)
        if i > 0:
            yield b","
        yield chunk.encode("utf-8")
    yield b"]"


_CSV_FIELDS = [
    "id", "resource_type", "resource_type_name", "source_id", "source_name",
    "name", "description", "search_text", "file_name", "file_path", "file_size",
    "file_type", "width", "height", "thumbnail_path", "group_id", "group_path",
    "created_by", "updated_by", "created_at", "updated_at", "tags",
]


def export_csv_stream(items: List[dict]) -> Generator[bytes, None, None]:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_CSV_FIELDS)
    yield output.getvalue().encode("utf-8-sig")
    output.seek(0)
    output.truncate(0)

    for item in items:
        row = []
        for field in _CSV_FIELDS:
            val = item.get(field)
            if field == "tags" and isinstance(val, list):
                row.append(";".join(val))
            elif val is None:
                row.append("")
            else:
                row.append(str(val))
        writer.writerow(row)
        yield output.getvalue().encode("utf-8")
        output.seek(0)
        output.truncate(0)


def export_zip_stream(
    items: List[dict],
    file_entries: List[Tuple[str, str]],
    thumb_entries: List[Tuple[str, str]],
) -> Generator[bytes, None, None]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(items, ensure_ascii=False, indent=2))
        for abs_path, arcname in file_entries:
            try:
                zf.write(abs_path, arcname)
            except Exception as e:
                logger.warning("导出 ZIP 写入文件失败: %s, error=%s", abs_path, e)
        for abs_path, arcname in thumb_entries:
            try:
                zf.write(abs_path, arcname)
            except Exception as e:
                logger.warning("导出 ZIP 写入缩略图失败: %s, error=%s", abs_path, e)
    yield buf.getvalue()
