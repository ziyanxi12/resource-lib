import json
import logging
import os
import re
from typing import Optional

from app.config import settings

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


def build_component_text(component_name: str, canvas_name: str, variant_name: str) -> str:
    logger.debug(
        "[build_component_text] 入参: component_name=%r  canvas_name=%r  variant_name=%r",
        component_name, canvas_name, variant_name,
    )

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
        key_part, value = pair.split("=", 1)
        value = value.strip()
        zh = translations.get(pair, "") or translations.get(value, "")
        parts.append(f"{value} {zh}" if zh else value)

    result = " ".join(p for p in parts if p)
    logger.debug("[build_component_text] 输出: %r", result)
    return result


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
    logger.debug(
        "[build_icon_text] 入参: category=%r  chinese_name=%r  name=%r  english_name=%r  description=%r",
        category, chinese_name, name, english_name, description,
    )

    parts = [
        category or "",
        chinese_name or "",
        _process_english_name(name),
        _process_english_name(english_name),
        _process_description(description),
    ]
    result = " ".join(p for p in parts if p)
    logger.debug("[build_icon_text] 输出: %r", result)
    return result
