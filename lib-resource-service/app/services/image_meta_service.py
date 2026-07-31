"""
缩略图尺寸读取工具。
用于在 width/height 缺失时，从已存储的缩略图文件懒读取像素尺寸并回写数据库。
"""
import logging
import os
import re
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


def read_thumbnail_dimensions(thumbnail_rel_path: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    从缩略图文件读取像素尺寸，返回 (width, height)。
    支持 PNG/JPEG/WEBP/GIF（Pillow）和 SVG（解析 width/height 或 viewBox）。
    文件不存在或读取失败时返回 None，不抛异常。
    """
    if not thumbnail_rel_path:
        return None

    abs_path = os.path.abspath(os.path.join(settings.FILE_ROOT_DIR, thumbnail_rel_path))
    if not os.path.isfile(abs_path):
        logger.warning("缩略图文件不存在: %s", thumbnail_rel_path)
        return None

    ext = thumbnail_rel_path.rsplit(".", 1)[-1].lower() if "." in thumbnail_rel_path else ""

    try:
        if ext == "svg":
            return _read_svg_dimensions(abs_path)
        return _read_raster_dimensions(abs_path)
    except Exception as e:
        logger.warning("读取缩略图尺寸失败: %s, error: %s", thumbnail_rel_path, e)
        return None


def _read_raster_dimensions(abs_path: str) -> Optional[Tuple[float, float]]:
    from PIL import Image
    with Image.open(abs_path) as img:
        w, h = img.size
        return float(w), float(h)


def _read_svg_dimensions(abs_path: str) -> Optional[Tuple[float, float]]:
    tree = ET.parse(abs_path)
    root = tree.getroot()
    attrs = root.attrib

    w = _parse_svg_length(attrs.get("width"))
    h = _parse_svg_length(attrs.get("height"))
    if w is not None and h is not None and w > 0 and h > 0:
        return w, h

    # 回退 viewBox: "min-x min-y width height"
    viewbox = attrs.get("viewBox")
    if viewbox:
        parts = re.split(r"[\s,]+", viewbox.strip())
        if len(parts) == 4:
            try:
                vw, vh = float(parts[2]), float(parts[3])
                if vw > 0 and vh > 0:
                    return vw, vh
            except ValueError:
                pass
    return None


def _parse_svg_length(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    # 去除单位（px/pt/em/等），取数值部分
    m = re.match(r"^([0-9]*\.?[0-9]+)", value.strip())
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None
