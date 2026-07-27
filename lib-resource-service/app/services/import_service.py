"""
全量批量导入服务

从 ZIP 包解析 config.json，在指定来源的默认分组下递归创建分组树及资源。
config.json 格式：
{
    "group": [
        {
            "label": "分组名",
            "data": [ { ...data 项... } ],
            "children": [ { "label": "子分组", "data": [] } ]
        }
    ]
}
data 项字段与 ResourceUpload.tsx 模板一致：
    name, file_name, file_path, thumbnail_path, description, tags, search_text, raw_data
"""

import json
import logging
import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource, ResourceGroup
from app.services import group_service, resource_service
from app.services.upload_service import get_file_dir
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)


def _get_or_create_default_group(
    db: Session, resource_type: ResourceType, source_id: int
) -> ResourceGroup:
    """查找指定来源+类型下的默认分组，不存在则创建。"""
    default_group = (
        db.query(ResourceGroup)
        .filter(
            ResourceGroup.resource_type == int(resource_type),
            ResourceGroup.source_id == source_id,
            ResourceGroup.is_default == 1,
            ResourceGroup.parent_id.is_(None),
        )
        .first()
    )
    if default_group:
        return default_group
    return group_service.create_group(
        db,
        resource_type=int(resource_type),
        name="默认分组",
        parent_id=None,
        source_id=source_id,
    )


def _resolve_ext(filename: str, default: str = "bin") -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else default


def _save_item(
    db: Session,
    item: Dict[str, Any],
    group_id: int,
    resource_type: ResourceType,
    source_id: int,
    extract_dir: str,
    file_dir_name: str,
    file_dir: str,
    thumb_dir: str,
    thumb_relative_prefix: str,
) -> Resource:
    """
    处理单条 data 项：复制文件（或使用外部链接），构建 Resource 并 add+flush。
    返回已 flush 的 Resource（含 id）。
    """
    file_uuid = str(uuid.uuid4())

    file_path_in_zip = item.get("file_path")
    file_url = item.get("file_url")
    if not file_path_in_zip and not file_url:
        raise ValueError("file_path 和 file_url 至少填一个")

    # 保存资源文件
    if file_path_in_zip:
        src = os.path.join(extract_dir, file_path_in_zip)
        if not os.path.exists(src):
            raise FileNotFoundError(f"ZIP 内未找到文件: {file_path_in_zip}")

        original_name = item.get("file_name") or os.path.basename(file_path_in_zip)
        ext = _resolve_ext(original_name)
        file_name = f"{file_uuid}.{ext}"
        file_relative_path = f"{file_dir_name}/{file_name}"
        file_abs_path = os.path.join(file_dir, file_name)

        shutil.copy2(src, file_abs_path)
        file_size = os.path.getsize(file_abs_path)
        file_type = ext
    else:
        # 外部链接，无本地文件
        file_name = item.get("file_name")
        file_relative_path = None
        file_size = None
        file_type = None

    # 保存缩略图
    thumb_relative_path = None
    thumbnail_path_in_zip = item.get("thumbnail_path")
    if thumbnail_path_in_zip:
        thumb_src = os.path.join(extract_dir, thumbnail_path_in_zip)
        if not os.path.exists(thumb_src):
            raise FileNotFoundError(f"ZIP 内未找到缩略图: {thumbnail_path_in_zip}")

        thumb_ext = _resolve_ext(thumbnail_path_in_zip, default="png")
        thumb_name = f"{file_uuid}_thumb.{thumb_ext}"
        thumb_relative_path = f"{thumb_relative_prefix}/{thumb_name}"
        thumb_abs_path = os.path.join(thumb_dir, thumb_name)
        shutil.copy2(thumb_src, thumb_abs_path)

    data = {
        "resource_type": int(resource_type),
        "source_id": source_id,
        "name": item.get("name", ""),
        "file_name": file_name,
        "file_path": file_relative_path,
        "file_size": file_size,
        "file_type": file_type,
        "width": item.get("width"),
        "height": item.get("height"),
        "thumbnail_path": thumb_relative_path,
        "description": item.get("description"),
        "group_id": group_id,
        "search_text": item.get("search_text"),
        "raw_data": item.get("raw_data"),
        "tags": resource_service.normalize_tags(item.get("tags", [])),
        "data_updated_at": datetime.utcnow(),
    }
    resource = Resource(**data)
    db.add(resource)
    db.flush()
    return resource


def _process_group_node(
    db: Session,
    node: Dict[str, Any],
    parent_id: int,
    resource_type: ResourceType,
    source_id: int,
    extract_dir: str,
    file_dir_name: str,
    file_dir: str,
    thumb_dir: str,
    thumb_relative_prefix: str,
    stats: Dict[str, Any],
) -> None:
    """递归处理分组节点：创建分组 → 处理 data → 递归 children。"""
    label = node.get("label")
    if not label:
        stats["errors"].append({"label": label, "reason": "缺少 label 字段"})
        return

    try:
        new_group = group_service.create_group(
            db,
            resource_type=int(resource_type),
            name=label,
            parent_id=parent_id,
            source_id=source_id,
        )
    except ValueError as e:
        stats["errors"].append({"label": label, "reason": f"创建分组失败: {e}"})
        return
    stats["groups_created"] += 1

    # 处理当前分组的 data 项
    for idx, item in enumerate(node.get("data", []) or []):
        item_name = item.get("name", f"第{idx + 1}项")
        try:
            resource = _save_item(
                db,
                item,
                new_group.id,
                resource_type,
                source_id,
                extract_dir,
                file_dir_name,
                file_dir,
                thumb_dir,
                thumb_relative_prefix,
            )
            stats["resources_created"] += 1
            stats["new_resource_ids"].append(resource.id)
        except Exception as e:
            logger.warning("导入资源失败: name=%s, err=%s", item_name, e)
            stats["errors"].append(
                {"group": label, "name": item_name, "reason": str(e)}
            )

    # 递归处理子分组
    for child in node.get("children", []) or []:
        _process_group_node(
            db,
            child,
            new_group.id,
            resource_type,
            source_id,
            extract_dir,
            file_dir_name,
            file_dir,
            thumb_dir,
            thumb_relative_prefix,
            stats,
        )


def full_batch_import(
    db: Session,
    source_id: int,
    resource_type: ResourceType,
    zip_bytes: bytes,
    skip_vector: bool = False,
) -> Dict[str, Any]:
    """
    全量批量导入：解压 ZIP → 解析 config.json → 在默认分组下递归创建分组和资源。

    Returns:
        {
            "groups_created": int,
            "resources_created": int,
            "errors": List[dict],
        }
    """
    # 解压到临时目录
    with tempfile.TemporaryDirectory() as extract_dir:
        try:
            with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile as e:
            raise ValueError(f"无效的 ZIP 文件: {e}")

        config_path = os.path.join(extract_dir, "config.json")
        if not os.path.exists(config_path):
            raise ValueError("ZIP 包中未找到 config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"config.json 解析失败: {e}")

        group_list = config.get("group")
        if not isinstance(group_list, list):
            raise ValueError("config.json 的 group 字段必须为数组")

        # 文件存储目录准备
        file_dir_name = get_file_dir(resource_type)
        file_dir = os.path.join(settings.FILE_ROOT_DIR, file_dir_name)
        if resource_type == ResourceType.image:
            thumb_dir = file_dir
            thumb_relative_prefix = "image"
        else:
            thumb_dir = os.path.join(file_dir, "image")
            thumb_relative_prefix = f"{file_dir_name}/image"
        os.makedirs(file_dir, exist_ok=True)
        os.makedirs(thumb_dir, exist_ok=True)

        # 查找/创建默认分组
        default_group = _get_or_create_default_group(db, resource_type, source_id)

        stats: Dict[str, Any] = {
            "groups_created": 0,
            "resources_created": 0,
            "errors": [],
            "new_resource_ids": [],
        }

        # 递归处理每个根级 group 节点（作为默认分组的子分组）
        for node in group_list:
            _process_group_node(
                db,
                node,
                default_group.id,
                resource_type,
                source_id,
                extract_dir,
                file_dir_name,
                file_dir,
                thumb_dir,
                thumb_relative_prefix,
                stats,
            )

        # 单事务提交
        db.commit()

        # 向量同步
        if not skip_vector and stats["new_resource_ids"]:
            try:
                new_resources = (
                    db.query(Resource)
                    .filter(Resource.id.in_(stats["new_resource_ids"]))
                    .all()
                )
                for res in new_resources:
                    res.vector_text = resource_service.build_vector_text(res)
                db.commit()

                pairs = [(res, {}) for res in new_resources]
                ingest_vectors(resource_type, pairs, skip_vector=False)
                resource_service.batch_update_vector_time(
                    db, [r.id for r in new_resources]
                )
            except Exception as e:
                logger.warning("向量同步失败（不影响导入结果）: %s", e)

        stats.pop("new_resource_ids", None)
        logger.info(
            "全量导入完成: source_id=%s, type=%s, groups=%d, resources=%d, errors=%d",
            source_id,
            resource_type.name,
            stats["groups_created"],
            stats["resources_created"],
            len(stats["errors"]),
        )
        return stats
