import json
import logging
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

from app.config import settings

if TYPE_CHECKING:
    from app.enums import ResourceType
    from app.models.resource import Resource

logger = logging.getLogger(__name__)

_translations: Optional[dict] = None


def _load_translations() -> dict:
    global _translations
    if _translations is None:
        path = settings.TRANSLATION_FILE
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _translations = json.load(f)
        else:
            logger.warning("翻译文件不存在，属性值将不做中文翻译: %s", path)
            _translations = {}
    return _translations


# ──────────────────────────────────────────────────────────────────
# 各类型文本构建函数
# 签名统一：(resource: Resource, raw: dict) -> str
# raw 在 init 批量入库时携带原始 JSON 字段；PUT 更新时为 {}，fallback 到 ORM 关联
# ──────────────────────────────────────────────────────────────────

def build_component_text(component_name: str, canvas_name: str, variant_name: str) -> str:
    translations = _load_translations()
    clean_canvas = re.sub(r"^\d+\.", "", canvas_name or "").strip()
    clean_name   = re.sub(r"^\d+\.", "", component_name or "").strip()
    parts = [clean_name, clean_canvas]
    for pair in (variant_name or "").split(","):
        pair = pair.strip()
        if "=" not in pair:
            if pair:
                parts.append(pair)
            continue
        _, value = pair.split("=", 1)
        value = value.strip()
        zh = translations.get(pair, "") or translations.get(value, "")
        parts.append(f"{value} {zh}" if zh else value)
    return " ".join(p for p in parts if p)


def _process_english_name(english_name: str) -> str:
    if not english_name:
        return ""
    if "_" in english_name:
        name = english_name
        if name.startswith("ic_"):
            name = name[3:]
        return name.replace("_", " ")
    return english_name


def _process_description(description: str) -> str:
    if not description:
        return ""
    if re.search(r"[一-鿿]", description):
        return description
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", description)


def build_icon_text(category: str, chinese_name: str, name: str, english_name: str, description: str) -> str:
    parts = [
        category or "",
        chinese_name or "",
        _process_english_name(name),
        _process_english_name(english_name),
        _process_description(description),
    ]
    return " ".join(p for p in parts if p)


def _build_component_text_fn(resource: "Resource", raw: dict) -> str:
    cv = resource.component_variant
    component_name = raw.get("parent_name")  or (cv.component_name if cv else "") or ""
    canvas_name    = raw.get("canvas_name")  or (cv.canvas_name    if cv else "") or ""
    variant_name   = raw.get("variant_name") or (cv.name           if cv else "") or ""
    return build_component_text(component_name, canvas_name, variant_name)


def _build_component_metadata(resource: "Resource", raw: dict) -> dict:
    cv = resource.component_variant
    return {
        "name":           resource.name,
        "canvas_name":    raw.get("canvas_name")  or (cv.canvas_name    if cv else "") or "",
        "component_name": raw.get("parent_name")  or (cv.component_name if cv else "") or "",
        "domain":         raw.get("domain")        or (cv.domain         if cv else "") or "",
    }


def _build_icon_text_fn(resource: "Resource", raw: dict) -> str:
    ic = resource.icon_detail
    chinese_name = raw.get("chineseName") or (ic.chinese_name if ic else resource.name) or ""
    category     = raw.get("category")    or (ic.category     if ic else "") or ""
    name         = raw.get("name")        or (ic.name         if ic else "") or ""
    english_name = raw.get("englishName") or (ic.english_name if ic else "") or ""
    description  = resource.description   or ""
    return build_icon_text(category, chinese_name, name, english_name, description)


def _build_icon_metadata(resource: "Resource", raw: dict) -> dict:
    ic = resource.icon_detail
    return {
        "name":         resource.name,
        "description":  resource.description or "",
        "english_name": raw.get("englishName") or (ic.english_name if ic else "") or "",
        "category":     raw.get("category")    or (ic.category     if ic else "") or "",
    }


def _build_illus_text_fn(resource: "Resource", raw: dict) -> str:
    il = resource.illus_detail
    illus_id = raw.get("id") or (il.illus_id if il else "") or ""
    alias    = resource.name or ""
    desc     = resource.description or ""
    category = raw.get("category") or (il.category if il else "") or ""
    tags     = raw.get("tags") or (il.tags if il else []) or []
    tag_str  = " ".join(tags) if isinstance(tags, list) else str(tags)
    version  = raw.get("version") or (il.version if il else "") or ""
    theme    = raw.get("theme") or (il.theme if il else "") or ""
    return " ".join(p for p in [illus_id, alias, desc, category, tag_str, version, theme] if p)


def _build_illus_metadata(resource: "Resource", raw: dict) -> dict:
    il = resource.illus_detail
    return {
        "name":     resource.name,
        "category": raw.get("category") or (il.category if il else "") or "",
        "version":  raw.get("version") or (il.version if il else "") or "",
        "theme":    raw.get("theme")    or (il.theme    if il else "") or "",
    }


def _build_simple_text(resource: "Resource", raw: dict) -> str:
    return f"{resource.name} {resource.description or ''}".strip()


def _build_simple_metadata(resource: "Resource", raw: dict) -> dict:
    return {"name": resource.name, "description": resource.description or ""}


# ──────────────────────────────────────────────────────────────────
# VectorSpec 注册表
# ──────────────────────────────────────────────────────────────────

@dataclass
class VectorSpec:
    vec_type:       str
    build_text:     Callable[["Resource", dict], str]
    build_metadata: Callable[["Resource", dict], dict]
    get_data_id:    Callable[["Resource"], str]


def _build_registry() -> Dict:
    from app.enums import ResourceType
    return {
        ResourceType.component: VectorSpec(
            vec_type="component",
            build_text=_build_component_text_fn,
            build_metadata=_build_component_metadata,
            get_data_id=lambda res: res.component_variant.variant_key,
        ),
        ResourceType.icon: VectorSpec(
            vec_type="icon",
            build_text=_build_icon_text_fn,
            build_metadata=_build_icon_metadata,
            get_data_id=lambda res: str(res.icon_detail.icon_id),
        ),
        ResourceType.illus: VectorSpec(
            vec_type="illus",
            build_text=_build_illus_text_fn,
            build_metadata=_build_illus_metadata,
            get_data_id=lambda res: str(res.illus_detail.illus_id),
        ),
        ResourceType.template: VectorSpec(
            vec_type="template",
            build_text=_build_simple_text,
            build_metadata=_build_simple_metadata,
            get_data_id=lambda res: str(res.id),
        ),
        ResourceType.image: VectorSpec(
            vec_type="image",
            build_text=_build_simple_text,
            build_metadata=_build_simple_metadata,
            get_data_id=lambda res: str(res.id),
        ),
    }


_REGISTRY: Optional[Dict] = None


def get_registry() -> Dict:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


# ──────────────────────────────────────────────────────────────────
# 统一向量入库入口
# ──────────────────────────────────────────────────────────────────

def ingest_vectors(
    resource_type: "ResourceType",
    pairs: List[Tuple["Resource", dict]],
    *,
    skip_vector: bool = False,
) -> None:
    """
    批量向量入库，所有类型统一入口。
    pairs: [(Resource ORM 对象, 原始 raw dict), ...]
    raw 在 init 场景携带 JSON 原始字段；PUT 更新场景传 {} 即可。
    异常只 warning，不影响主流程。
    """
    if skip_vector or not settings.VECTOR_SERVICE_ENABLED:
        return
    spec = get_registry().get(resource_type)
    if spec is None:
        return
    if not pairs:
        return

    items = [
        {
            "data_id":  spec.get_data_id(res),
            "text":     spec.build_text(res, raw),
            "metadata": spec.build_metadata(res, raw),
        }
        for res, raw in pairs
    ]
    try:
        from app.clients import vector_client
        result = vector_client.ingest(spec.vec_type, items)
        logger.info(
            "向量入库完成 type=%s: 成功 %d 条，失败 %d 条",
            spec.vec_type, len(result["succeeded"]), len(result["failed"]),
        )
    except Exception as e:
        logger.warning("向量入库异常（不影响 DB）type=%s: %s", spec.vec_type, e)
