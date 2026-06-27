import json
import os
import re
from typing import Optional

from app.config import settings

_translations: Optional[dict] = None


def _load_translations() -> dict:
    global _translations
    if _translations is None:
        path = os.path.join(settings.FILE_ROOT_DIR, "component", "value_translations.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _translations = json.load(f)
        else:
            _translations = {}
    return _translations


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
        key_part, value = pair.split("=", 1)
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


def build_icon_text(name: str, english_name: str, description: str, category: str) -> str:
    parts = [
        name or "",
        _process_english_name(english_name),
        _process_description(description),
        category or "",
    ]
    return " ".join(p for p in parts if p)
