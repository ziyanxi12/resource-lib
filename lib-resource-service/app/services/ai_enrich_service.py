"""
AI 补充描述批量生成服务

核心功能：
1. 查询待处理的资源（ai_description IS NULL 且有预览图）
2. 并发调用图片理解模块生成视觉/场景描述
3. 写入 ai_description 字段 + 触发向量同步
4. 通过 task_registry 追踪进度，支持取消
"""

import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ResourceType
from app.models.resource import Resource, ResourceGroup
from app.services import ai_enrich_task_registry as task_registry

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Prompt 构建
# ──────────────────────────────────────────────────────────────────

_TYPE_DIMENSIONS = {
    ResourceType.icon: {
        "label": "图标",
        "dim2_label": "符号含义",
        "dim2_guidance": "图标表达什么物体或动作、线条风格（线性/填充/双色）、方向感",
    },
    ResourceType.illus: {
        "label": "插画",
        "dim2_label": "情绪氛围",
        "dim2_guidance": "传达什么情绪或故事感、装饰风格（扁平/手绘/3D/等距）",
    },
    ResourceType.image: {
        "label": "图片",
        "dim2_label": "画面主题",
        "dim2_guidance": "拍摄主体、场景类型、视觉氛围",
    },
    ResourceType.file: {
        "label": "文件",
        "dim2_label": "文件内容",
        "dim2_guidance": "文件类型、内容概要",
    },
}

_PROMPT_TEMPLATE = """你是设计资源库的语义索引工程师。请根据缩略图和元数据，为这个{type_label}生成一段用于向量搜索的精准描述。

请从以下三个维度组织内容：
1. 视觉特征：根据缩略图描述外观、色调、风格、构图或布局结构
2. {dim2_label}：{dim2_guidance}
3. 业务场景：最适合用在什么业务页面、模块或交互场景中

【输入信息】
- 资源类型：{type_label}
- 名称：{name}
- 分组路径：{group_path}
- 业务数据：{raw_data_json}

【输出要求】
- 60~100字中文，自然语言短语，空格分隔
- 关键词密集，使用用户实际会搜索的词汇（如"登录页""空状态""暖色调""提交按钮"）
- 只描述图中可见内容和合理推断的用途，不编造不存在的元素
- 直接输出描述文本，不加前缀说明，不加标点堆砌"""


def build_prompt(resource: Resource) -> str:
    """根据资源类型和元数据构建 LLM prompt"""
    rt = ResourceType(resource.resource_type)
    dims = _TYPE_DIMENSIONS.get(rt, _TYPE_DIMENSIONS[ResourceType.file])

    group_path = ""
    if resource.group:
        group_path = resource.group.real_path or ""

    raw_data_str = ""
    if resource.raw_data:
        try:
            raw_data_str = json.dumps(resource.raw_data, ensure_ascii=False)
        except Exception:
            raw_data_str = ""

    return _PROMPT_TEMPLATE.format(
        type_label=dims["label"],
        dim2_label=dims["dim2_label"],
        dim2_guidance=dims["dim2_guidance"],
        name=resource.name or "",
        group_path=group_path,
        raw_data_json=raw_data_str or "无",
    )


# ──────────────────────────────────────────────────────────────────
# 资源查询
# ──────────────────────────────────────────────────────────────────

def _resolve_image_path(resource: Resource) -> Optional[str]:
    """解析资源可用的图片路径（图片类型用原图，其他用缩略图）"""
    if resource.resource_type == int(ResourceType.image):
        rel_path = resource.file_path or resource.thumbnail_path
    else:
        rel_path = resource.thumbnail_path
    if not rel_path:
        return None
    abs_path = os.path.abspath(os.path.join(settings.FILE_ROOT_DIR, rel_path))
    if not os.path.isfile(abs_path):
        return None
    return abs_path


def get_pending_resources(
    db: Session,
    resource_type: ResourceType,
    source_id: Optional[int] = None,
    limit: Optional[int] = None,
    force: bool = False,
) -> List[Resource]:
    """查询待处理资源"""
    query = db.query(Resource).filter(
        Resource.resource_type == int(resource_type),
        Resource.is_deleted == 0,
    )
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    if not force:
        query = query.filter(Resource.ai_description.is_(None))

    query = query.order_by(Resource.id)
    if limit:
        query = query.limit(limit)
    return query.all()


def count_pending(
    db: Session,
    resource_type: ResourceType,
    source_id: Optional[int] = None,
    force: bool = False,
) -> int:
    """统计待处理数量（不 limit）"""
    query = db.query(Resource.id).filter(
        Resource.resource_type == int(resource_type),
        Resource.is_deleted == 0,
    )
    if source_id is not None:
        query = query.filter(Resource.source_id == source_id)

    if not force:
        query = query.filter(Resource.ai_description.is_(None))

    return query.count()


# ──────────────────────────────────────────────────────────────────
# 单条处理
# ──────────────────────────────────────────────────────────────────

def _process_one(resource_id: int, task_id: str) -> Tuple[bool, str, bool]:
    """
    处理单条资源（在 worker 线程中执行，独立 session）

    返回: (success, message, skipped)
    """
    from app.database import SessionLocal
    from app.clients import image_understanding
    from app.services.resource_service import build_vector_text

    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return False, "资源不存在", False

        image_path = _resolve_image_path(resource)
        if not image_path:
            resource.ai_description = ""
            resource.data_updated_at = datetime.now()
            db.commit()
            return True, "无可用预览图，标记为空串跳过", True

        if task_registry.is_cancelled(task_id):
            return False, "已取消", False

        prompt = build_prompt(resource)

        try:
            result = image_understanding.understand_image(
                image_path, prompt, image_is_base64=False
            )
        except NotImplementedError:
            return False, "图片理解模块未接入", False
        except Exception as e:
            return False, f"LLM 调用失败: {e}", False

        if not result or not result.strip():
            return False, "LLM 返回空结果", False

        resource.ai_description = result.strip()
        resource.data_updated_at = datetime.now()
        resource.vector_text = build_vector_text(resource)
        db.commit()
        return True, "成功", False

    except Exception as e:
        db.rollback()
        logger.error("处理资源失败 resource_id=%d: %s", resource_id, e)
        return False, str(e), False
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────
# 批量入口
# ──────────────────────────────────────────────────────────────────

def enrich_batch(
    db: Session,
    task_id: str,
    resource_type: ResourceType,
    source_id: Optional[int] = None,
    limit: Optional[int] = None,
    concurrency: int = 1,
    force: bool = False,
) -> None:
    """
    批量生成 AI 描述（在后台线程中执行）

    1. 查询待处理资源
    2. ThreadPoolExecutor 并发调 LLM
    3. 每条写 ai_description + data_updated_at
    4. 末尾触发向量增量同步
    """
    task_registry.update_task(task_id, status="running", message="正在查询待处理资源")

    resources = get_pending_resources(db, resource_type, source_id, limit, force)
    total = len(resources)

    if not resources:
        task_registry.update_task(
            task_id, status="success", total=0, processed=0,
            message="无待处理资源"
        )
        return

    resource_ids = [r.id for r in resources]
    task_registry.update_task(task_id, total=total, message=f"开始处理 {total} 条资源")

    logger.info(
        "AI enrich 开始: task=%s type=%s total=%d concurrency=%d force=%s",
        task_id, resource_type.name, total, concurrency, force,
    )

    succeeded = 0
    failed = 0
    skipped = 0

    try:
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
            future_to_id = {
                executor.submit(_process_one, rid, task_id): rid
                for rid in resource_ids
            }

            for future in as_completed(future_to_id):
                rid = future_to_id[future]

                if task_registry.is_cancelled(task_id):
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                try:
                    success, msg, was_skipped = future.result()
                except Exception as e:
                    success, msg, was_skipped = False, str(e), False

                task_registry.increment_task(task_id, processed=1)
                if was_skipped:
                    skipped += 1
                    task_registry.increment_task(task_id, skipped=1)
                elif success:
                    succeeded += 1
                    task_registry.increment_task(task_id, succeeded=1)
                else:
                    failed += 1
                    task_registry.increment_task(task_id, failed=1)
                    task_registry.add_error(task_id, rid, msg)

    except Exception as e:
        logger.exception("AI enrich 异常: task=%s", task_id)
        task_registry.update_task(
            task_id, status="failed", message=f"任务异常: {e}"
        )
        return

    final_status = "cancelled" if task_registry.is_cancelled(task_id) else "success"
    message = f"完成：成功 {succeeded}，失败 {failed}，跳过 {skipped}，共 {total}"

    task_registry.update_task(
        task_id, status=final_status, message=message
    )

    logger.info(
        "AI enrich 完成: task=%s status=%s total=%d success=%d failed=%d skipped=%d",
        task_id, final_status, total, succeeded, failed, skipped,
    )

    # 触发向量增量同步（ai_description 已写入，data_updated_at 已更新）
    if succeeded > 0 and settings.VECTOR_SERVICE_ENABLED:
        try:
            from app.services.vector_sync_service import sync_vectors_by_type
            sync_db = None
            try:
                from app.database import SessionLocal as _SL
                sync_db = _SL()
                result = sync_vectors_by_type(sync_db, resource_type, source_id)
                logger.info("向量同步完成: task=%s %s", task_id, result.get("message", ""))
            finally:
                if sync_db:
                    sync_db.close()
        except Exception as e:
            logger.warning("向量同步失败（不影响 AI 描述结果）: task=%s %s", task_id, e)
