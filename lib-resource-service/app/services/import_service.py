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
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource, ResourceGroup
from app.services import resource_service
from app.services import import_task_registry
from app.services.upload_service import get_file_dir
from app.services.vector_text_builder import ingest_vectors

logger = logging.getLogger(__name__)

# Phase 3 分块查询大小，避免 SQLite IN 子句参数上限 (默认 999)
_CHUNK_SIZE = 500


class ImportCancelled(Exception):
    """用户请求取消导入时抛出"""
    pass


def _create_group_no_commit(
    db: Session,
    resource_type: int,
    name: str,
    parent_id,
    source_id: int,
) -> ResourceGroup:
    """
    内联版 create_group：构建 ResourceGroup 并 add+flush，不 commit。
    复制原有分组创建的 level/real_path/sort_order 计算逻辑，
    但全部用 flush 代替 commit，减少 SQLite 锁竞争。
    """
    if parent_id is None:
        existing_root = db.query(ResourceGroup).filter(
            ResourceGroup.resource_type == resource_type,
            ResourceGroup.source_id == source_id,
            ResourceGroup.parent_id.is_(None),
        ).first()
        if existing_root:
            raise ValueError("该来源下已存在默认分组")

    if parent_id:
        parent = db.query(ResourceGroup).filter(ResourceGroup.id == parent_id).first()
        if not parent:
            raise ValueError(f"Parent group {parent_id} not found")
        level = parent.level + 1
        real_path = f"{parent.real_path}/{name}"
        is_default = 0
    else:
        level = 0
        real_path = name
        is_default = 1 if name == "默认分组" else 0

    # 内联 get_next_sort_order
    q = db.query(func.max(ResourceGroup.sort_order)).filter(
        ResourceGroup.resource_type == resource_type
    )
    if source_id is not None:
        q = q.filter(ResourceGroup.source_id == source_id)
    if parent_id is None:
        q = q.filter(ResourceGroup.parent_id.is_(None))
    else:
        q = q.filter(ResourceGroup.parent_id == parent_id)
    sort_order = (q.scalar() or -1) + 1

    group = ResourceGroup(
        resource_type=resource_type,
        source_id=source_id,
        name=name,
        parent_id=parent_id,
        level=level,
        real_path=real_path,
        sort_order=sort_order,
        is_default=is_default,
    )
    db.add(group)
    db.flush()
    return group


def _get_or_create_default_group(
    db: Session, resource_type: ResourceType, source_id: int
) -> ResourceGroup:
    """查找指定来源+类型下的默认分组，不存在则创建（不 commit，由调用方统一提交）。"""
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
    return _create_group_no_commit(
        db,
        resource_type=int(resource_type),
        name="默认分组",
        parent_id=None,
        source_id=source_id,
    )


def _resolve_ext(filename: str, default: str = "") -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else default


def _precopy_files(
    node: Dict[str, Any],
    extract_dir: str,
    file_dir_name: str,
    file_dir: str,
    thumb_dir: str,
    thumb_relative_prefix: str,
    errors: list,
    group_label: str = "",
    task_id: Optional[str] = None,
) -> list:
    """
    Phase 1：遍历分组节点的 data 项，复制文件到 storage（无 DB 事务）。
    将复制后的路径信息写回 item dict（_saved_* 前缀），供 Phase 2 使用。
    返回处理后的 data 列表（只含成功项，跳过的无效项不在此列表中）。
    """
    processed_data = []
    for idx, item in enumerate(node.get("data", []) or []):
        if import_task_registry.is_cancelled(task_id):
            raise ImportCancelled()
        item_name = item.get("name", f"第{idx + 1}项")
        file_uuid = str(uuid.uuid4())

        file_path_in_zip = item.get("file_path")
        file_url = item.get("file_url")
        if not file_path_in_zip and not file_url:
            errors.append({"group": group_label, "name": item_name, "reason": "file_path 和 file_url 至少填一个"})
            continue

        saved = {"_file_uuid": file_uuid}

        # 复制资源文件
        if file_path_in_zip:
            src = os.path.join(extract_dir, file_path_in_zip)
            if not os.path.exists(src):
                errors.append({"group": group_label, "name": item_name, "reason": f"ZIP 内未找到文件: {file_path_in_zip}"})
                continue
            ext = _resolve_ext(os.path.basename(file_path_in_zip))
            disk_name = f"{file_uuid}.{ext}" if ext else file_uuid
            file_relative_path = f"{file_dir_name}/{disk_name}"
            file_abs_path = os.path.join(file_dir, disk_name)
            shutil.copy2(src, file_abs_path)
            saved["_file_name"] = item.get("file_name")
            saved["_file_relative_path"] = file_relative_path
            saved["_file_size"] = os.path.getsize(file_abs_path)
            saved["_file_type"] = ext
        else:
            saved["_file_name"] = item.get("file_name")
            saved["_file_relative_path"] = None
            saved["_file_size"] = None
            saved["_file_type"] = None

        # 复制缩略图
        thumbnail_path_in_zip = item.get("thumbnail_path")
        if thumbnail_path_in_zip:
            thumb_src = os.path.join(extract_dir, thumbnail_path_in_zip)
            if not os.path.exists(thumb_src):
                errors.append({"group": group_label, "name": item_name, "reason": f"ZIP 内未找到缩略图: {thumbnail_path_in_zip}"})
                continue
            thumb_ext = _resolve_ext(thumbnail_path_in_zip, default="png")
            thumb_name = f"{file_uuid}_thumb.{thumb_ext}"
            saved["_thumb_relative_path"] = f"{thumb_relative_prefix}/{thumb_name}"
            shutil.copy2(thumb_src, os.path.join(thumb_dir, thumb_name))
        else:
            saved["_thumb_relative_path"] = None

        processed_data.append((item, saved))

    return processed_data


def _precopy_tree(
    nodes: list,
    extract_dir: str,
    file_dir_name: str,
    file_dir: str,
    thumb_dir: str,
    thumb_relative_prefix: str,
    errors: list,
    task_id: Optional[str] = None,
) -> int:
    """
    Phase 1 递归：遍历整棵 group 树，预复制所有文件。
    将处理结果挂到每个节点["_processed"]上（[(item, saved)] 列表），
    供 Phase 2 直接从节点取用，避免迭代器错位。
    返回成功处理的文件总数。
    """
    total = 0

    def _walk(node, parent_label=""):
        nonlocal total
        label = node.get("label")
        if not label:
            errors.append({"label": label, "reason": "缺少 label 字段"})
            return

        full_label = f"{parent_label}/{label}" if parent_label else label
        processed = _precopy_files(
            node, extract_dir, file_dir_name, file_dir, thumb_dir, thumb_relative_prefix, errors, full_label, task_id
        )
        node["_processed"] = processed
        total += len(processed)

        for child in node.get("children", []) or []:
            _walk(child, full_label)

    for node in nodes:
        _walk(node)

    return total


def _create_db_records(
    db: Session,
    nodes: list,
    parent_id: int,
    resource_type: ResourceType,
    source_id: int,
    stats: Dict[str, Any],
    task_id: Optional[str] = None,
) -> None:
    """
    Phase 2：快速创建 DB 记录（无文件 I/O，事务极短）。
    递归创建分组树，从每个节点的 _processed 列表创建资源。
    资源按分组批量 add_all + 单次 flush，避免逐条 flush 的性能问题。
    """

    def _walk(node, pid):
        if import_task_registry.is_cancelled(task_id):
            raise ImportCancelled()
        label = node.get("label")
        if not label:
            return

        try:
            new_group = _create_group_no_commit(
                db,
                resource_type=int(resource_type),
                name=label,
                parent_id=pid,
                source_id=source_id,
            )
        except ValueError as e:
            stats["errors"].append({"label": label, "reason": f"创建分组失败: {e}"})
            return
        stats["groups_created"] += 1

        # 从节点取 Phase 1 预处理的列表（只含成功项）
        processed_items: List[Tuple[dict, dict]] = node.get("_processed", [])
        batch: List[Resource] = []
        for item, saved in processed_items:
            data = {
                "resource_type": int(resource_type),
                "source_id": source_id,
                "name": item.get("name", ""),
                "file_name": saved.get("_file_name"),
                "file_path": saved.get("_file_relative_path"),
                "file_size": saved.get("_file_size"),
                "file_type": saved.get("_file_type"),
                "width": item.get("width"),
                "height": item.get("height"),
                "thumbnail_path": saved.get("_thumb_relative_path"),
                "description": item.get("description"),
                "group_id": new_group.id,
                "search_text": item.get("search_text"),
                "raw_data": item.get("raw_data"),
                "tags": resource_service.normalize_tags(item.get("tags", [])),
                "data_updated_at": datetime.utcnow(),
            }
            batch.append(Resource(**data))
            stats["resources_created"] += 1

        if batch:
            db.add_all(batch)
            db.flush()
            stats["new_resource_ids"].extend(r.id for r in batch)

        for child in node.get("children", []) or []:
            _walk(child, new_group.id)

    for node in nodes:
        _walk(node, parent_id)


def full_batch_import(
    db: Session,
    source_id: int,
    resource_type: ResourceType,
    zip_bytes: bytes,
    skip_vector: bool = False,
    task_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    全量批量导入：三阶段处理（预复制文件 → 快速DB入库 → 向量同步）。

    task_id 非空时，在各阶段边界上报进度到 import_task_registry，
    并在循环中检查取消标志。

    Returns:
        {
            "groups_created": int,
            "resources_created": int,
            "errors": List[dict],
        }
    """

    def _report(phase: int = None, phase_label: str = None, **extra):
        if not task_id:
            return
        kwargs = {}
        if phase is not None:
            kwargs["phase"] = phase
        if phase_label is not None:
            kwargs["phase_label"] = phase_label
        kwargs.update(extra)
        import_task_registry.update_task(task_id, **kwargs)

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

        stats: Dict[str, Any] = {
            "groups_created": 0,
            "resources_created": 0,
            "errors": [],
            "new_resource_ids": [],
        }

        # ===== Phase 1：预复制所有文件（无 DB 事务，零锁）=====
        _report(status="running", phase=1, phase_label="解压并复制文件")
        total_copied = _precopy_tree(
            group_list,
            extract_dir,
            file_dir_name,
            file_dir,
            thumb_dir,
            thumb_relative_prefix,
            stats["errors"],
            task_id=task_id,
        )
        logger.info("Phase 1 完成: 预复制 %d 个文件, %d 个错误", total_copied, len(stats["errors"]))

        # ===== Phase 2：快速创建 DB 记录（批量 add_all，毫秒级）=====
        _report(phase=2, phase_label="创建数据库记录")
        default_group = _get_or_create_default_group(db, resource_type, source_id)
        _create_db_records(
            db,
            group_list,
            default_group.id,
            resource_type,
            source_id,
            stats,
            task_id=task_id,
        )
        db.commit()
        logger.info("Phase 2 完成: %d 个分组, %d 个资源", stats["groups_created"], stats["resources_created"])
        _report(phase_label="数据库入库完成", groups_created=stats["groups_created"],
                resources_created=stats["resources_created"], errors=stats["errors"])

        # ===== Phase 3：向量同步（事务外）=====
        if not skip_vector and stats["new_resource_ids"]:
            _report(phase=3, phase_label="向量同步")
            try:
                if import_task_registry.is_cancelled(task_id):
                    raise ImportCancelled()

                # 分块查询，避免 SQLite IN 子句参数上限
                new_resources: List[Resource] = []
                all_ids = stats["new_resource_ids"]
                for i in range(0, len(all_ids), _CHUNK_SIZE):
                    chunk = all_ids[i:i + _CHUNK_SIZE]
                    new_resources.extend(
                        db.query(Resource).filter(Resource.id.in_(chunk)).all()
                    )

                for res in new_resources:
                    res.vector_text = resource_service.build_vector_text(res)
                db.commit()

                pairs = [(res, {}) for res in new_resources]
                ingest_vectors(resource_type, pairs, skip_vector=False)
                resource_service.batch_update_vector_time(
                    db, [r.id for r in new_resources]
                )
            except ImportCancelled:
                raise
            except Exception as e:
                logger.warning("向量同步失败（不影响导入结果）: %s", e)

        stats.pop("new_resource_ids", None)
        _report(phase=4, phase_label="完成", status="success")
        logger.info(
            "全量导入完成: source_id=%s, type=%s, groups=%d, resources=%d, errors=%d",
            source_id,
            resource_type.name,
            stats["groups_created"],
            stats["resources_created"],
            len(stats["errors"]),
        )
        return stats
