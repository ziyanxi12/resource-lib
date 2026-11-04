"""设计系统 zip 包解析服务（octo-design-zip/1 格式）。

zip 结构（requirement/1.md）：
    xxx.zip
    ├─ assets/
    │  ├─ components/     递归目录 → html 文件（html 文件名 = 组件名）
    │  └─ patterns/       递归目录 → html 文件
    ├─ DESIGN.md          设计展示页数据（复用 design_system_md 解析）
    └─ skill-design.zip   附件（原样保留，落盘后可经 /static 下载）

职责：
- 安全校验：zip slip（`..`/绝对路径/反斜杠/symlink）、zip bomb（条目数/解压总大小/压缩比）
- 解压到临时目录（zip 字节先写临时文件再解压，对齐需求「先 zip 落盘，再解压」）
- 定位 DESIGN.md / skill-design.zip（支持单层包裹目录：根下唯一目录时向内找一层）
- 递归扫描 assets/components、assets/patterns → 目录树（层级保留在 group 字段），
  叶子 html 按 template.html 既有协议生成 components/patterns 区块（内嵌 html 源码，
  模板 sandbox iframe 直接 srcdoc 渲染；同目录 css/scss 一并内嵌）
- DESIGN.md 解析产物（design_system_md.parse_md）与本区块合并为最终 design-system.json dict

解析失败抛 ZipPackageError(ValueError)（路由层转 400）。
"""

import io
import json
import os
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services import design_system_md

# ─────────────────────────── 限额与常量 ───────────────────────────

MAX_ZIP_BYTES = 200 * 1024 * 1024           # 上传 zip 上限（与分片阈值配套，api.md 契约）
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 解压后总大小上限（zip bomb 防护）
MAX_ZIP_ENTRIES = 5000                      # zip 内条目数上限（含目录）
MAX_COMPRESS_RATIO = 100                    # 单文件压缩比上限（>100 且 >1MB 视为异常）
MAX_EMBED_HTML_BYTES = 2 * 1024 * 1024      # 单个 html 内嵌 design-system.json 上限（超出只存路径）

CHUNK_SIZE = 5 * 1024 * 1024                # 每片 5MB（S3 multipart 同款下限）
UPLOADS_REL_DIR = "design-systems/uploads"  # 分片临时目录（FILE_ROOT_DIR 下）
UPLOAD_TTL_SECONDS = 24 * 3600              # 孤儿分片清理阈值

SKILL_ZIP_NAME = "skill-design.zip"

# macOS 打包垃圾与隐藏文件，直接跳过
_JUNK_RE = re.compile(r"^(__MACOSX/|Thumbs\.db|\._|\.DS_Store)")

# Unix 文件类型位（external_attr 高 16 位）：拒绝 symlink/设备/管道/socket
_FORBIDDEN_MODES = {0o120000, 0o140000, 0o060000, 0o020000, 0o010000}


class ZipPackageError(ValueError):
    """zip 包结构/安全校验失败（路由层转 400，detail 为错误说明）"""


# ─────────────────────────── 安全校验与解压 ───────────────────────────

def _normalize_name(raw: str) -> str:
    """zip entry 名归一化：反斜杠转 /、去头部 ./、折叠连续 /。"""
    name = raw.replace("\\", "/")
    while name.startswith("./"):
        name = name[2:]
    name = re.sub(r"/{2,}", "/", name)
    return name


def _validate_member(name: str, info: zipfile.ZipInfo) -> None:
    """单个 entry 校验：路径注入与危险文件类型。失败抛 ZipPackageError。"""
    if _JUNK_RE.match(name):
        raise ZipPackageError("包含不支持的系统文件：%s" % name)
    if not name or name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        raise ZipPackageError("zip 内不允许绝对路径：%s" % name)
    if ".." in name.split("/"):
        raise ZipPackageError("zip 内不允许相对路径回溯（..）：%s" % name)
    mode = (info.external_attr >> 16) & 0o170000
    if mode in _FORBIDDEN_MODES:
        raise ZipPackageError("zip 内不允许符号链接/设备等特殊文件：%s" % name)


def validate_zip_bytes(content: bytes) -> None:
    """上传入口校验：zip 魔数、大小、条目数、解压总大小与压缩比。"""
    if len(content) > MAX_ZIP_BYTES:
        raise ZipPackageError("zip 包超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise ZipPackageError("文件不是合法的 zip 包")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ZIP_ENTRIES:
                raise ZipPackageError("zip 内条目数超过 %d 上限" % MAX_ZIP_ENTRIES)
            total = 0
            for info in infos:
                name = _normalize_name(info.filename)
                _validate_member(name, info)
                if info.is_dir():
                    continue
                total += info.file_size
                if total > MAX_UNCOMPRESSED_BYTES:
                    raise ZipPackageError("解压后总大小超过 %dMB 上限" % (MAX_UNCOMPRESSED_BYTES // 1024 // 1024))
                if (info.file_size > 10 * 1024 * 1024
                        and info.compress_size > 0
                        and info.file_size > info.compress_size * MAX_COMPRESS_RATIO):
                    raise ZipPackageError("压缩比异常（疑似 zip bomb）：%s" % info.filename)
    except zipfile.BadZipFile as e:
        raise ZipPackageError("zip 包损坏：%s" % e)


def extract_zip(content: bytes, dest_dir: str) -> None:
    """安全解压：zip 字节先落盘临时文件，再逐 entry 校验落盘（不用 extractall）。"""
    fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        with zipfile.ZipFile(tmp_path) as zf:
            for info in zf.infolist():
                name = _normalize_name(info.filename)
                _validate_member(name, info)
                target = os.path.join(dest_dir, *name.split("/"))
                if info.is_dir():
                    os.makedirs(target, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    # 逐块拷贝，同时强制解压总量上限（防 info.file_size 伪造）
                    written = 0
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > MAX_UNCOMPRESSED_BYTES:
                            raise ZipPackageError("解压后总大小超过上限：%s" % name)
                        out.write(chunk)
    except zipfile.BadZipFile as e:
        raise ZipPackageError("zip 包损坏：%s" % e)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─────────────────────────── zip 内容定位 ───────────────────────────

def _list_rel(root: str) -> List[str]:
    """目录下所有文件相对路径（排除垃圾文件），排序保证稳定。"""
    out = []
    for dirpath, _dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        if rel_dir == ".":
            rel_dir = ""
        for fn in filenames:
            rel = "%s/%s" % (rel_dir, fn) if rel_dir else fn
            if _JUNK_RE.match(rel):
                continue
            out.append(rel)
    return sorted(out)


def locate_root_entries(dest_dir: str) -> Tuple[str, Optional[str]]:
    """定位有效根（DESIGN.md 所在层），返回 (有效根绝对路径, skill-design.zip 绝对路径或 None)。

    支持两种布局：entry 直接在 zip 根；或根下只有一个目录（打包工具常见包裹目录）时向内一层。
    """
    root = dest_dir
    if "DESIGN.md" not in _list_rel(root):
        tops = {f.split("/")[0] for f in _list_rel(root)}
        if len(tops) == 1:
            candidate = os.path.join(dest_dir, next(iter(tops)))
            if os.path.isdir(candidate) and "DESIGN.md" in _list_rel(candidate):
                root = candidate
    files = _list_rel(root)
    if "DESIGN.md" not in files:
        raise ZipPackageError("zip 包内缺少 DESIGN.md（应在 zip 根目录，octo-design-md/1 格式）")
    skill_path = os.path.join(root, SKILL_ZIP_NAME) if SKILL_ZIP_NAME in files else None
    return root, skill_path


# ─────────────────────────── assets 树扫描 ───────────────────────────

def _scan_group(root: str, group: str) -> List[Dict]:
    """扫描 assets/{group} 递归目录，返回叶子条目（已按路径排序）。

    name  html 文件名去扩展（= 组件名）；group 目录层级数组；
    path  相对有效根的路径；html/css 为绝对路径（css = 同目录 css/scss，一并内嵌）。
    """
    base = os.path.join(root, "assets", group)
    items = []
    if not os.path.isdir(base):
        return items
    for dirpath, _dirnames, filenames in sorted(os.walk(base)):
        rel_dir = os.path.relpath(dirpath, base).replace(os.sep, "/")
        levels = [p for p in rel_dir.split("/") if p not in (".", "")]
        for fn in sorted(filenames):
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext != "html":
                continue
            parts = ["assets", group] + levels + [fn]
            items.append({
                "name": fn[: -len(".html")],
                "group": levels,
                "path": "/".join(parts),
                "html": os.path.join(dirpath, fn),
                "css": [
                    os.path.join(dirpath, c)
                    for c in sorted(filenames)
                    if c.lower().endswith((".css", ".scss"))
                ],
            })
    return items


def _embed_file(abs_path: str, lang: str, rel_path: str) -> Dict:
    """读文件生成模板 files[] 条目（超 MAX_EMBED_HTML_BYTES 只存路径不内嵌）。"""
    entry = OrderedDict()
    entry["lang"] = lang
    entry["path"] = rel_path
    if os.path.getsize(abs_path) <= MAX_EMBED_HTML_BYTES:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            entry["code"] = f.read()
    return entry


def _uniquify_ids(items: List[Dict]) -> None:
    """不同目录同名 html：id 追加序号保证唯一（name 保留原名）。"""
    seen: Dict[str, int] = {}
    for it in items:
        base_id = re.sub(r"[^a-z0-9-]", "-", it["name"].lower()).strip("-") or "comp"
        seen[base_id] = seen.get(base_id, 0) + 1
        it["id"] = base_id if seen[base_id] == 1 else "%s-%d" % (base_id, seen[base_id])


def build_assets_blocks(root: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """assets 目录 → (components 区块, patterns 区块)（template.html 既有协议）。

    - components：items[].source.files[{lang: html/css, code}] —— 模板 sandbox srcdoc 渲染
    - patterns：items[] 元信息 + view.cards[].states.html 内嵌源码 —— 模板 iframe srcdoc 渲染
    - 层级：目录层级保留在 group 数组，同时拼进 name（模板组件导航为平铺，层级进 name 可读）
    无 assets 或无 html 时返回 (None, None)。
    """
    comp_items = _scan_group(root, "components")
    pat_items = _scan_group(root, "patterns")

    components = None
    if comp_items:
        _uniquify_ids(comp_items)
        items = []
        for it in comp_items:
            files = [_embed_file(it["html"], "html", it["path"])]
            for css in it["css"]:
                rel = it["path"][: -len(os.path.basename(it["html"]))] + os.path.basename(css)
                files.append(_embed_file(css, "css", rel))
            items.append(OrderedDict([
                ("id", it["id"]),
                ("name", " / ".join(it["group"] + [it["name"]]) if it["group"] else it["name"]),
                ("desc", it["path"]),
                ("group", it["group"]),
                ("source", OrderedDict([
                    ("status", "found"),
                    ("files", files),
                ])),
            ]))
        components = OrderedDict([
            ("title", "组件"),
            ("desc", "%d 个组件 · 来自 assets/components" % len(items)),
            ("items", items),
        ])

    patterns = None
    if pat_items:
        _uniquify_ids(pat_items)
        items = []
        cards = []
        for it in pat_items:
            display_name = " / ".join(it["group"] + [it["name"]]) if it["group"] else it["name"]
            items.append(OrderedDict([
                ("id", it["id"]),
                ("name", display_name),
                ("label", it["path"]),
                ("group", it["group"]),
            ]))
            html_file = _embed_file(it["html"], "html", it["path"])
            code = html_file.get("code")
            state = OrderedDict([("meta", it["path"])])
            if code is not None:
                state["html"] = code
            cards.append(OrderedDict([
                ("id", it["id"]),
                ("states", OrderedDict([("default", state)])),
            ]))
        patterns = OrderedDict([
            ("title", "布局 Pattern"),
            ("desc", "%d 个 Pattern · 来自 assets/patterns" % len(items)),
            ("items", items),
            ("view", OrderedDict([("cards", cards)])),
        ])

    return components, patterns


# ─────────────────────────── 组装 ───────────────────────────

def parse_md_root(root: str) -> Dict:
    """读有效根下的 DESIGN.md → design-system.json 同构 dict（无 assets 区块）。

    解析失败抛 ZipPackageError；结构合法性（id/name/token 区块）由
    design_system_service.validate_design_system_json 校验（解析与校验分离）。
    """
    with open(os.path.join(root, "DESIGN.md"), "rb") as f:
        md_bytes = f.read()
    try:
        return design_system_md.parse_md(md_bytes.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise ZipPackageError("DESIGN.md 必须是 UTF-8 文本：%s" % e)
    except ValueError as e:
        raise ZipPackageError(str(e))


def merge_assets(data: Dict, root: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """扫描有效根的 assets 目录，把 components/patterns 区块合并进 data（就地修改）。

    返回 (components 区块, patterns 区块)（无则均为 None，便于调用方记 coverage）。
    """
    components, patterns = build_assets_blocks(root)
    if components is not None:
        data["components"] = components
    if patterns is not None:
        data["patterns"] = patterns
    coverage = data.setdefault("coverage", OrderedDict())
    coverage["components"] = components is not None
    coverage["patterns"] = patterns is not None
    data["meta"] = data.get("meta") or OrderedDict()
    data["meta"]["source_file"] = "zip（DESIGN.md + assets）"
    return components, patterns


def parse_zip(content: bytes) -> Dict:
    """zip 字节 → design-system.json 同构 dict（MD 解析 + assets 区块合并）。

    便捷入口（测试与预览用）；正式入库走 design_system_service.import_zip
    （需要保留解压临时目录以持久化 assets 文件，本函数临时目录随返回即清理）。
    """
    validate_zip_bytes(content)
    with tempfile.TemporaryDirectory(prefix="ds-zip-") as dest:
        extract_zip(content, dest)
        root, _skill_path = locate_root_entries(dest)
        data = parse_md_root(root)
        merge_assets(data, root)
        return data


def parse_zip_info(content: bytes) -> Dict:
    """parse 预览接口用：解析结果 + 统计（不落库）。"""
    validate_zip_bytes(content)
    with tempfile.TemporaryDirectory(prefix="ds-zip-") as dest:
        extract_zip(content, dest)
        root, skill_path = locate_root_entries(dest)
        data = parse_md_root(root)
        merge_assets(data, root)
        skill_size = os.path.getsize(skill_path) if skill_path else 0
    comp_items = ((data.get("components") or {}).get("items")) or []
    pat_items = ((data.get("patterns") or {}).get("items")) or []
    levels = sorted({
        " / ".join(it.get("group") or [])
        for it in comp_items + pat_items
        if it.get("group")
    })
    return {
        "ds": data,
        "stats": {
            "slug": data.get("id") or "",
            "name": data.get("name") or "",
            "components": len(comp_items),
            "patterns": len(pat_items),
            "levels": levels,
            "zip_size": len(content),
        },
        "skill_zip": {
            "present": bool(skill_path),
            "filename": SKILL_ZIP_NAME if skill_path else None,
            "size": skill_size,
        },
    }


# ─────────────────────────── 分片上传 ───────────────────────────

_UPLOAD_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def uploads_root() -> str:
    return os.path.join(settings.FILE_ROOT_DIR, UPLOADS_REL_DIR)


def _upload_dir(upload_id: str) -> str:
    if not _UPLOAD_ID_RE.match(upload_id):
        raise ZipPackageError("upload_id 非法")
    return os.path.join(uploads_root(), upload_id)


def cleanup_stale_uploads() -> int:
    """清理超过 TTL 的分片目录（init 时顺带执行，无需后台任务）。返回清理个数。"""
    root = uploads_root()
    if not os.path.isdir(root):
        return 0
    removed = 0
    now = time.time()
    for name in os.listdir(root):
        if not _UPLOAD_ID_RE.match(name):
            continue
        path = os.path.join(root, name)
        try:
            if now - os.path.getmtime(path) > UPLOAD_TTL_SECONDS:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        except OSError:
            continue
    return removed


def upload_init(filename: str, size: int) -> Dict:
    """创建分片上传会话：{upload_id, chunk_size, chunk_count}。"""
    cleanup_stale_uploads()
    if not size or size <= 0:
        raise ZipPackageError("文件大小非法")
    if size > MAX_ZIP_BYTES:
        raise ZipPackageError("zip 包超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    upload_id = uuid.uuid4().hex
    os.makedirs(_upload_dir(upload_id), exist_ok=True)
    meta = {
        "filename": os.path.basename(filename or "upload.zip"),
        "size": size,
        "chunk_size": CHUNK_SIZE,
        "chunk_count": (size + CHUNK_SIZE - 1) // CHUNK_SIZE,
        "created_at": time.time(),
        "status": "uploading",
    }
    with open(os.path.join(_upload_dir(upload_id), "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return {"upload_id": upload_id, "chunk_size": CHUNK_SIZE, "chunk_count": meta["chunk_count"]}


def _load_upload_meta(upload_id: str) -> Dict:
    path = _upload_dir(upload_id)
    meta_file = os.path.join(path, "meta.json")
    if not os.path.isfile(meta_file):
        raise ZipPackageError("上传会话不存在或已过期：%s" % upload_id)
    with open(meta_file, encoding="utf-8") as f:
        meta = json.load(f)
    if meta.get("status") != "uploading":
        raise ZipPackageError("上传会话已结束：%s" % upload_id)
    return meta


def upload_chunk(upload_id: str, index: int, body: bytes) -> Dict:
    """写入第 index 片（raw binary body），返回 {received, size}。"""
    meta = _load_upload_meta(upload_id)
    if not isinstance(index, int) or index < 0 or index >= meta["chunk_count"]:
        raise ZipPackageError("分片序号越界：%s（共 %d 片）" % (index, meta["chunk_count"]))
    expected = meta["chunk_size"] if index < meta["chunk_count"] - 1 else meta["size"] - meta["chunk_size"] * (meta["chunk_count"] - 1)
    if len(body) != expected:
        raise ZipPackageError("分片大小不符：期望 %d 字节，收到 %d" % (expected, len(body)))
    with open(os.path.join(_upload_dir(upload_id), "%06d.part" % index), "wb") as f:
        f.write(body)
    return {"received": index, "size": len(body)}


def upload_merge(upload_id: str) -> Tuple[bytes, str]:
    """合并分片 → (zip 字节, 原文件名)；校验完整性后标记会话完成。"""
    path = _upload_dir(upload_id)
    meta = _load_upload_meta(upload_id)
    total = 0
    for index in range(meta["chunk_count"]):
        part = os.path.join(path, "%06d.part" % index)
        if not os.path.isfile(part):
            raise ZipPackageError("分片缺失：第 %d/%d 片" % (index + 1, meta["chunk_count"]))
        total += os.path.getsize(part)
    if total != meta["size"]:
        raise ZipPackageError("分片合并后大小不符：期望 %d，实际 %d" % (meta["size"], total))
    buf = bytearray()
    for index in range(meta["chunk_count"]):
        with open(os.path.join(path, "%06d.part" % index), "rb") as f:
            buf.extend(f.read())
    meta["status"] = "merged"
    with open(os.path.join(path, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return bytes(buf), meta.get("filename") or "upload.zip"


def upload_discard(upload_id: str) -> None:
    """异常路径兜底：清理分片会话目录（幂等）。"""
    if _UPLOAD_ID_RE.match(upload_id):
        shutil.rmtree(_upload_dir(upload_id), ignore_errors=True)
