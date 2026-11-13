"""设计系统五部件解析服务（octo-design-parts/1 格式）。

五部件（multipart 各自独立上传、独立成败，失败部件忽略并回报错误）：
    design_md    DESIGN.md 原文：UTF-8 校验后原样存 {slug}/source.md
                 （展示端概览 fetch 后 markdown 渲染，不再机器解析）
    tokens       tokens.json（唯一数据源）：UTF-8 + JSON 校验 → convert_tokens_to_legacy
                 转 老 design-system.json 区块结构 + 原件存 {slug}/tokens.json
    components   组件 zip：根须含 components/ 目录；扫描子目录层级 = group、
                 html 文件名 = 组件名，落盘 {slug}/assets/components/**
    patterns     Pattern zip：根须含 patterns/ 目录，同组件包规则，
                 落盘 {slug}/assets/patterns/**
    skill        skill 包 zip：第一层须含 SKILL.md（frontmatter name 入 skill_name），
                 原样落盘 {slug}/{原文件名}

components/patterns zip 兼容同名双层嵌套（components/components/按钮/Button.html）：
locate_group_base 循环剥离同名子层后以最内层为扫描基目录（group/path 归一化，
不含重复层）。

职责：
- 安全校验：zip slip（`..`/绝对路径/反斜杠/symlink）、zip bomb（条目数/解压总大小/
  压缩比）、同名冲突条目（目录/文件同名及大小写变体）
- 打包垃圾静默丢弃：macOS/Windows 压缩工具产物（__MACOSX/、._* AppleDouble、
  .DS_Store、Thumbs.db，含嵌套路径）不报错、不落盘、不参与解析——用户本机
  「右键压缩」产生的 zip 必然携带，属正常现象而非非法内容
- 解压到临时目录（zip 字节先写临时文件再解压，对齐需求「先落盘，再解压」）
- 各部件独立校验 / 解析原语（本模块不落盘到 {slug}/，正式入库走
  design_system_service.import_parts 编排）
- components/patterns 区块按 template.html 既有协议生成（items[].height 固定 160）
- skill 包严格校验：第一层 SKILL.md + frontmatter name 非空 ≤255 字符

解析失败抛 ZipPackageError(ValueError)（路由层转 400 / 部件级错误回报）。
"""

import io
import json
import logging
import os
import re
import shutil
import tempfile
import zipfile
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from app.services import design_system_md

logger = logging.getLogger(__name__)

# ─────────────────────────── 限额与常量 ───────────────────────────

MAX_ZIP_BYTES = 200 * 1024 * 1024           # 单部件上传上限（zip 部件；api.md 契约）
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 解压后总大小上限（zip bomb 防护）
MAX_ZIP_ENTRIES = 5000                      # zip 内条目数上限（含目录）
MAX_COMPRESS_RATIO = 100                    # 单文件压缩比上限（>100 且 >1MB 视为异常）
MAX_EMBED_HTML_BYTES = 2 * 1024 * 1024      # 单个 html 内嵌 design-system.json 上限（超出只存路径）
DEFAULT_ROW_HEIGHT = 160                    # items[].height 默认行高（展示端表格行预览高度，预留修正通道）
MAX_SKILL_MD_BYTES = 1024 * 1024            # skill 包内 SKILL.md 读取上限（防 zip bomb，超出拒绝）
MAX_SKILL_NAME_LEN = 255                    # SKILL.md frontmatter name 字段长度上限（对齐 DB 列宽）

# skill 包落盘时不得与 design-systems/{slug}/ 下的系统保留文件重名（大小写不敏感）
RESERVED_SKILL_NAMES = {"source.zip", "source.md", "design-system.json", "tokens.json"}

# 部件 → 展示名（错误信息用）
GROUP_LABEL = {"components": "组件", "patterns": "Pattern"}

# Unix 文件类型位（external_attr 高 16 位）：拒绝 symlink/设备/管道/socket
_FORBIDDEN_MODES = {0o120000, 0o140000, 0o060000, 0o020000, 0o010000}


def _is_junk_entry(name: str) -> bool:
    """macOS / Windows 打包垃圾条目：任一路径段为 `__MACOSX` / `.DS_Store` / `Thumbs.db`
    / 以 `._` 开头（AppleDouble 资源叉伴随文件）。

    用户本机「右键压缩」产生的 zip 必然携带（`__MACOSX/._components` 等），属正常现象
    而非非法内容——一律**静默丢弃**：不报错、不落盘、不参与条目统计与扫描。
    按路径段判断，覆盖顶层（`__MACOSX/…`）与嵌套（`components/.DS_Store`、
    `components/按钮/._Button.html`）两种位置。
    """
    return any(
        p == "__MACOSX" or p == ".DS_Store" or p == "Thumbs.db" or p.startswith("._")
        for p in name.split("/")
        if p
    )


class ZipPackageError(ValueError):
    """zip 包结构/安全校验失败（路由层转 400 / 部件级错误回报）"""


# ─────────────────────────── 安全校验与解压 ───────────────────────────

def _normalize_name(raw: str) -> str:
    """zip entry 名归一化：cp437→UTF-8 名字修正、反斜杠转 /、去头部 ./、折叠连续 /。"""
    # Python zipfile 对未置 EFS 位（UTF-8 flag）的条目名按 cp437 解码——ditto（mac
    # 命令行打包）及部分 Windows 工具产出「UTF-8 字节但未标记」的名字，中文名会变乱码
    # （如「表单」→ 'Φí¿σìò'）→ 尝试还原为 UTF-8。正常 EFS 名（中文字符不在 cp437 里，
    # encode 报错回落原样）、纯 ASCII（恒等）、真 cp437 西文名（通常非法 UTF-8，解码
    # 报错回落原样）均不受影响。
    try:
        raw = raw.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    name = raw.replace("\\", "/")
    while name.startswith("./"):
        name = name[2:]
    name = re.sub(r"/{2,}", "/", name)
    return name


def _validate_member(name: str, info: zipfile.ZipInfo) -> None:
    """单个 entry 校验：路径注入与危险文件类型。失败抛 ZipPackageError。

    打包垃圾（__MACOSX/._* 等）不在此拦截——由 validate_zip_bytes / extract_zip
    在调用前经 _is_junk_entry 静默过滤。
    """
    if not name or name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        raise ZipPackageError("zip 内不允许绝对路径：%s" % name)
    if ".." in name.split("/"):
        raise ZipPackageError("zip 内不允许相对路径回溯（..）：%s" % name)
    mode = (info.external_attr >> 16) & 0o170000
    if mode in _FORBIDDEN_MODES:
        raise ZipPackageError("zip 内不允许符号链接/设备等特殊文件：%s" % name)


def validate_zip_bytes(content: bytes) -> None:
    """上传入口校验：zip 魔数、大小、条目数、解压总大小与压缩比、同名冲突条目。"""
    if len(content) > MAX_ZIP_BYTES:
        raise ZipPackageError("zip 包超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise ZipPackageError("文件不是合法的 zip 包")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ZIP_ENTRIES:
                raise ZipPackageError("zip 内条目数超过 %d 上限" % MAX_ZIP_ENTRIES)
            # 同名冲突体检：归一化 + casefold 比较（跨平台一致——macOS/Windows 大小写不敏感文件系统上
            # 「Assets/」与「assets」也是同一路径）。同名（含大小写变体）既是目录又是文件 → 拒绝；
            # 否则解压时 open(目录路径) 会抛未捕获的 IsADirectoryError → 500。
            # 同名重复「文件」条目放行（后解压覆盖，无崩溃、语义明确）。
            # 打包垃圾条目（__MACOSX/._* 等）静默跳过：不计数、不落盘、不参与冲突判定
            # （垃圾永不落盘，与真实条目不可能产生文件系统冲突）。
            seen = {}  # casefold(归一化名，去尾斜杠) -> (归一化名, 是否目录)
            total = 0
            junk = 0
            for info in infos:
                name = _normalize_name(info.filename)
                if _is_junk_entry(name):
                    junk += 1
                    continue
                _validate_member(name, info)
                key = name.casefold().rstrip("/")
                prev = seen.get(key)
                if prev is not None and prev[1] != info.is_dir():
                    raise ZipPackageError(
                        "zip 内存在同名冲突条目：「%s」（%s）与「%s」（%s）——目录与文件不能同名，"
                        "请检查打包结构后重新打包"
                        % (prev[0], "目录" if prev[1] else "文件",
                           name, "目录" if info.is_dir() else "文件"))
                if prev is None:
                    seen[key] = (name, info.is_dir())
                if info.is_dir():
                    continue
                total += info.file_size
                if total > MAX_UNCOMPRESSED_BYTES:
                    raise ZipPackageError("解压后总大小超过 %dMB 上限" % (MAX_UNCOMPRESSED_BYTES // 1024 // 1024))
                if (info.file_size > 10 * 1024 * 1024
                        and info.compress_size > 0
                        and info.file_size > info.compress_size * MAX_COMPRESS_RATIO):
                    raise ZipPackageError("压缩比异常（疑似 zip bomb）：%s" % info.filename)
            if junk:
                logger.info("[zip-validate] 静默丢弃 %d 个打包垃圾条目（__MACOSX/ ._* / .DS_Store / Thumbs.db）", junk)
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
                if _is_junk_entry(name):
                    continue  # 打包垃圾静默跳过，不落盘
                _validate_member(name, info)
                target = os.path.join(dest_dir, *name.split("/"))
                if info.is_dir():
                    os.makedirs(target, exist_ok=True)
                    continue
                # 动态兜底（防御纵深——同名冲突已在 validate 阶段拦截；此处捕获漏网的
                # 文件系统特定冲突，转 400 而非未捕获的 IsADirectoryError/FileExistsError → 500）
                try:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                except FileExistsError:
                    raise ZipPackageError(
                        "zip 内存在同名冲突条目：「%s」既是文件又是目录，请检查打包结构后重新打包" % name)
                if os.path.isdir(target):
                    raise ZipPackageError(
                        "zip 内存在同名冲突条目：「%s」（目录与文件同名），请检查打包结构后重新打包" % name)
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


# ─────────────────────────── 部件 1：DESIGN.md ───────────────────────────

def parse_design_md_bytes(content: bytes) -> None:
    """DESIGN.md 部件校验：必须是 UTF-8 文本（原文原样存 source.md，不机器解析）。

    失败抛 ZipPackageError（该部件失败，其余部件不受影响）。
    """
    if len(content) > MAX_ZIP_BYTES:
        raise ZipPackageError("DESIGN.md 超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ZipPackageError("DESIGN.md 必须是 UTF-8 文本：%s" % e)


# ─────────────────────────── 部件 2：tokens.json ───────────────────────────

def parse_tokens_bytes(content: bytes) -> Tuple[Dict, Dict]:
    """tokens.json 部件校验 + 转换：返回 (原件 dict, legacy 转换 dict)。

    - **唯一数据源**：UTF-8（容忍 BOM）+ JSON 语法错误是硬错误 → ZipPackageError；
      顶层必须是 JSON 对象；分组结构零校验（color/… 缺失 → 模板渲染空态）
    - legacy 转换（convert_tokens_to_legacy）：tokens.json → 老 design-system.json
      区块结构（模板与存量零改动）；多余分组（fontScale 等）顶层原样保留、暂不渲染
    """
    if len(content) > MAX_ZIP_BYTES:
        raise ZipPackageError("tokens.json 超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    try:
        text = content.decode("utf-8-sig")  # 容忍 BOM
    except UnicodeDecodeError as e:
        raise ZipPackageError("tokens.json 必须是 UTF-8 文本：%s" % e)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as e:
        raise ZipPackageError("tokens.json 不是合法 JSON：%s" % e)
    if not isinstance(raw, dict):
        raise ZipPackageError("tokens.json 顶层必须是 JSON 对象，收到：%s" % type(raw).__name__)
    return raw, convert_tokens_to_legacy(raw)


def _first_theme_id(color: dict) -> str:
    """颜色主题感知：取 themes[0].id（缺省 'light'）。多主题扩展点：将来出现 dark 等主题时，
    token 形态扩展为 values 全量保留 + 模板主题切换器，改此入口即可。"""
    themes = color.get("themes")
    if isinstance(themes, list) and themes and isinstance(themes[0], dict) and themes[0].get("id"):
        return str(themes[0]["id"])
    return "light"


def _theme_value(value, theme_id: str):
    """value 是主题映射（{light: ...}）时取指定主题（缺则取首个）；普通单值原样返回。"""
    if isinstance(value, dict):
        if theme_id in value:
            return value[theme_id]
        for v in value.values():
            return v
        return ""
    return value


def _px_num(value):
    """'8px' / '0' / '16' → float；解析失败返回 None。"""
    s = str(value).strip()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def convert_tokens_to_legacy(tokens: dict) -> dict:
    """tokens.json（octo-design-parts 数据源）→ 老 design-system.json 区块结构。

    模板与存量系统零改动：转换产物即模板原生渲染的老结构。
    - color：tokens[].value 按主题映射 → 主题感知取首主题；themes 原样保留；
      groups = [{title, tokens: [{name, token: usage, value, label: name}]}]
    - type（families 映射 + groups[].styles）→ typography（families/weights/scale：
      style → {name, size, lineHeight, weight, family: families[group.family], desc: group.name}）
    - size → spacing、radius → radius（value 数值化）；shadow → shadow（value 原样 css 串）
    - 装不进老结构的分组（fontScale/fontScaleRegular/opacity/other）：**顶层原样保留，暂不渲染**
    - name/id（预留）/cover/version/meta：顶层原样
    - 源分组缺 tokens / 空列表 → 对应区块不生成（模板渲染空态）
    """
    out = dict(tokens)  # 浅拷贝：多余分组与元数据原样保留

    # ── 颜色 ──
    color = tokens.get("color")
    if isinstance(color, dict):
        theme_id = _first_theme_id(color)
        mapped = []
        for t in color.get("tokens") or []:
            if not isinstance(t, dict):
                continue
            mapped.append({
                "name": str(t.get("name") or ""),
                "token": str(t.get("usage") or ""),
                "value": _theme_value(t.get("value"), theme_id),
                "label": str(t.get("name") or ""),
            })
        if mapped:
            out["color"] = {
                "title": str(color.get("title") or "颜色"),
                "desc": color.get("desc") or "",
                "themes": color.get("themes") or [],
                "groups": [{"title": "全部颜色", "desc": "", "tokens": mapped}],
                "rules": color.get("rules") or [],
            }
        else:
            out.pop("color", None)

    # ── 字体：type → typography ──
    if not isinstance(tokens.get("typography"), dict):
        ty = tokens.get("type") if isinstance(tokens.get("type"), dict) else {}
        families_map = ty.get("families") if isinstance(ty.get("families"), dict) else {}
        families = [str(v) for v in families_map.values()]
        scale, weights = [], []
        for g in ty.get("groups") or []:
            if not isinstance(g, dict):
                continue
            fam_key = str(g.get("family") or "")
            for st in g.get("styles") or []:
                if not isinstance(st, dict):
                    continue
                scale.append({
                    "name": str(st.get("name") or ""),
                    "size": _px_num(st.get("fontSize")) or 0,
                    "lineHeight": _px_num(st.get("lineHeight")) or 0,
                    "weight": st.get("fontWeight") or 400,
                    "family": families_map.get(fam_key, fam_key) or "",
                    "token": str(st.get("name") or ""),
                    "desc": str(g.get("name") or ""),
                })
                w = str(st.get("fontWeight") or "")
                if w and w not in weights:
                    weights.append(w)
        if families or scale:
            out["typography"] = {
                "title": str(ty.get("title") or "字体"),
                "desc": ty.get("desc") or "",
                "families": families,
                "weights": weights,
                "scale": scale,
                "rules": ty.get("rules") or [],
            }
        else:
            out.pop("typography", None)

    # ── 间距：size → spacing（value 数值化）──
    if not isinstance(tokens.get("spacing"), dict):
        sz = tokens.get("size") if isinstance(tokens.get("size"), dict) else {}
        mapped = []
        for t in sz.get("tokens") or []:
            if isinstance(t, dict):
                mapped.append({
                    "name": str(t.get("name") or ""),
                    "value": _px_num(t.get("value")),
                    "desc": t.get("usage") or "",
                })
        mapped = [t for t in mapped if t["value"] is not None]
        if mapped:
            out["spacing"] = {
                "title": str(sz.get("title") or "间距"),
                "desc": sz.get("desc") or "",
                "tokens": mapped,
                "rules": sz.get("rules") or [],
            }
        else:
            out.pop("spacing", None)

    # ── 圆角：radius（value 数值化）──
    rad = tokens.get("radius")
    if isinstance(rad, dict):
        mapped = []
        for t in rad.get("tokens") or []:
            if not isinstance(t, dict):
                continue
            num = _px_num(t.get("value"))
            if num is None:
                continue
            mapped.append({"name": str(t.get("name") or ""), "value": num, "desc": t.get("usage") or ""})
        if mapped:
            out["radius"] = {
                "title": str(rad.get("title") or "圆角"),
                "desc": rad.get("desc") or "",
                "tokens": mapped,
                "rules": rad.get("rules") or [],
            }
        else:
            out.pop("radius", None)

    # ── 阴影：shadow（value 原样 css 串）──
    sh = tokens.get("shadow")
    if isinstance(sh, dict):
        mapped = []
        for t in sh.get("tokens") or []:
            if isinstance(t, dict):
                mapped.append({
                    "name": str(t.get("name") or ""),
                    "value": str(t.get("value") or ""),
                    "desc": t.get("usage") or "",
                })
        if mapped:
            out["shadow"] = {
                "title": str(sh.get("title") or "阴影"),
                "desc": sh.get("desc") or "",
                "tokens": mapped,
                "rules": sh.get("rules") or [],
            }
        else:
            out.pop("shadow", None)

    return out


# ─────────────────────────── 部件 3/4：组件包 / Pattern 包 ───────────────────────────

def locate_group_base(extract_root: str, group: str) -> Tuple[str, bool]:
    """定位 {group} 扫描基目录，返回 (基目录绝对路径, 是否发生同名嵌套剥离)。

    - zip 根必须有 {group}/ 目录（否则该部件失败——ZipPackageError）
    - 兼容同名多层嵌套（components/components/按钮/Button.html）：循环剥离同名子层，
      以最内层为扫描基目录（group 层级与存储 path 均按剥离后的相对路径归一化）
    """
    label = GROUP_LABEL.get(group, group)
    base = os.path.join(extract_root, group)
    if not os.path.isdir(base):
        raise ZipPackageError("%s包 zip 根目录缺少 %s/ 目录（%s 包内条目应组织在该目录下）"
                              % (label, group, label))
    nested = False
    while os.path.isdir(os.path.join(base, group)):
        nested = True
        base = os.path.join(base, group)
        logger.warning("[parts-import] %s包内检测到同名嵌套目录 %s/，向内剥离一层（当前基目录：%s）",
                       label, group, base)
    return base, nested


def _scan_group(base: str, group: str) -> List[Dict]:
    """扫描基目录递归结构，返回叶子条目（已按路径排序）。

    name  html 文件名去扩展（= 组件名）；group 目录层级数组（基目录之下）；
    path  归一化存储路径 assets/{group}/…（不含同名嵌套剥离层）；
    html/css 为绝对路径（css = 同目录 css/scss，一并内嵌）。
    打包垃圾文件名（._* / .DS_Store / Thumbs.db）防御性过滤（正常在解压阶段已丢弃）。
    """
    items = []
    if not os.path.isdir(base):
        return items
    for dirpath, _dirnames, filenames in sorted(os.walk(base)):
        rel_dir = os.path.relpath(dirpath, base).replace(os.sep, "/")
        levels = [p for p in rel_dir.split("/") if p not in (".", "")]
        for fn in sorted(filenames):
            if _is_junk_entry(fn):
                continue
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


def _build_components_block(items: List[Dict]) -> Optional[Dict]:
    """扫描条目 → components 区块（template.html 既有协议）。

    items[].source.files[{lang: html/css, code}] —— 模板 sandbox srcdoc 渲染；
    层级：目录层级保留在 group 数组，同时拼进 name（模板组件导航为平铺，层级进 name 可读）。
    """
    if not items:
        return None
    _uniquify_ids(items)
    out_items = []
    for it in items:
        files = [_embed_file(it["html"], "html", it["path"])]
        for css in it["css"]:
            rel = it["path"][: -len(os.path.basename(it["html"]))] + os.path.basename(css)
            files.append(_embed_file(css, "css", rel))
        out_items.append(OrderedDict([
            ("id", it["id"]),
            ("name", " / ".join(it["group"] + [it["name"]]) if it["group"] else it["name"]),
            ("desc", it["path"]),
            ("group", it["group"]),
            ("height", DEFAULT_ROW_HEIGHT),
            ("source", OrderedDict([
                ("status", "found"),
                ("files", files),
            ])),
        ]))
    return OrderedDict([
        ("title", "组件"),
        ("desc", "%d 个组件 · 来自 assets/components" % len(out_items)),
        ("items", out_items),
    ])


def _build_patterns_block(items: List[Dict]) -> Optional[Dict]:
    """扫描条目 → patterns 区块（template.html 既有协议）。

    items[] 元信息 + view.cards[].states.html 内嵌源码 —— 模板 iframe srcdoc 渲染。
    """
    if not items:
        return None
    _uniquify_ids(items)
    out_items = []
    cards = []
    for it in items:
        display_name = " / ".join(it["group"] + [it["name"]]) if it["group"] else it["name"]
        out_items.append(OrderedDict([
            ("id", it["id"]),
            ("name", display_name),
            ("label", it["path"]),
            ("group", it["group"]),
            ("height", DEFAULT_ROW_HEIGHT),
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
    return OrderedDict([
        ("title", "Pattern"),
        ("desc", "%d 个 Pattern · 来自 assets/patterns" % len(out_items)),
        ("items", out_items),
        ("view", OrderedDict([("cards", cards)])),
    ])


def ingest_group_zip(content: bytes, group: str, dst_group_dir: str) -> Dict:
    """组件包 / Pattern 包部件导入：校验 + 解压 + 定位（含同名嵌套剥离）+ 扫描 + 落盘。

    - 安全校验同上传入口（validate_zip_bytes：slip/bomb/条目数/同名冲突）
    - zip 根须含 {group}/ 目录（否则该部件失败）；同名嵌套层（components/components/）
      循环剥离后以最内层为扫描基目录
    - 落盘：dst_group_dir（= design-systems/{slug}/assets/{group}）整体替换——
      先清空旧子树再拷入新内容；本函数任何一步抛错时目标子树不受影响
    - 返回 {"block": 区块 dict 或 None（无 html）, "count": 叶子 html 数, "nested": 是否剥离}
    """
    label = GROUP_LABEL.get(group, group)
    validate_zip_bytes(content)
    with tempfile.TemporaryDirectory(prefix="ds-group-") as tmp:
        extract_zip(content, tmp)
        base, nested = locate_group_base(tmp, group)
        items = _scan_group(base, group)
        block = _build_components_block(items) if group == "components" else _build_patterns_block(items)
        # 落盘：先验证后拷贝（copytree 失败属于系统级异常，不属于部件校验失败）
        if os.path.isdir(dst_group_dir):
            shutil.rmtree(dst_group_dir)
        os.makedirs(os.path.dirname(dst_group_dir), exist_ok=True)
        shutil.copytree(base, dst_group_dir)
        logger.info("[parts-import] %s包导入完成：%d 个 html，%s",
                    label, len(items), "检测到同名嵌套目录并已剥离" if nested else "标准结构")
        return {"block": block, "count": len(items), "nested": nested}


# ─────────────────────────── 部件 5：skill 包 ───────────────────────────

def extract_skill_name(skill_zip_path: str) -> str:
    """解析 skill 包，返回根级 SKILL.md frontmatter 的 name（技能名）。

    严格校验（ZipPackageError → 路由层转部件级错误回报）：
    - SKILL.md 必须在附件 zip 第一层（根级），嵌套包裹目录视为缺失
    - 必须有 YAML frontmatter（--- ... ---）且 name 字段非空、≤255 字符
    - 附件本身必须是合法 zip；SKILL.md 成员 ≤1MB（防嵌套 zip bomb）
    """
    try:
        zf = zipfile.ZipFile(skill_zip_path)
    except zipfile.BadZipFile:
        raise ZipPackageError("skill 包不是合法的 zip 包（第一层须含 SKILL.md）")
    with zf:
        if "SKILL.md" not in zf.namelist():
            raise ZipPackageError("skill 包内缺少 SKILL.md（须在 zip 第一层，不允许嵌套）")
        info = zf.getinfo("SKILL.md")
        if info.file_size > MAX_SKILL_MD_BYTES:
            raise ZipPackageError("skill 包内 SKILL.md 超过 1MB 上限")
        try:
            with zf.open(info) as f:
                text = f.read(MAX_SKILL_MD_BYTES + 1).decode("utf-8", errors="replace")
        except (zipfile.BadZipFile, OSError, EOFError) as e:
            raise ZipPackageError("skill 包内 SKILL.md 读取失败：%s" % e)
    try:
        fm = design_system_md.parse_frontmatter(text)
    except ValueError:
        raise ZipPackageError("skill 包内 SKILL.md 缺少 frontmatter（--- name: 技能名 --- 头部块）")
    name = str(fm.get("name") or "").strip()
    if not name:
        raise ZipPackageError("skill 包内 SKILL.md 缺少 name 字段（技能名）")
    if len(name) > MAX_SKILL_NAME_LEN:
        raise ZipPackageError("skill 包内 SKILL.md 的 name 超过 %d 字符" % MAX_SKILL_NAME_LEN)
    return name


def parse_skill_zip_bytes(content: bytes) -> str:
    """skill 包部件校验（zip 字节 → 技能名）。失败抛 ZipPackageError（该部件失败）。"""
    if len(content) > MAX_ZIP_BYTES:
        raise ZipPackageError("skill 包超过 %dMB 上限" % (MAX_ZIP_BYTES // 1024 // 1024))
    validate_zip_bytes(content)
    fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        return extract_skill_name(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─────────────────────────── 存储版瘦身 ───────────────────────────

def slim_for_storage(data: Dict) -> None:
    """存储版 design-system.json 瘦身（只影响入库落盘）。

    展示端模板 iframe src 直连 /static 资产（不再 srcdoc/内嵌源码渲染），
    存储版只保留路径字段即可：
    - components：items[].source.files 只留 html 条目并去掉内嵌 code（css 条目随沙箱渲染一并废弃）
    - patterns：view.cards[].states[*] 去掉内嵌 html（meta 已是部件内路径，展示端据此推 URL）
    - overview：去掉内嵌 markdown（展示端概览 fetch source.md=design_md_url 落盘件）
    - 其余字段（title/desc/items[].desc/items[].label/height 等）全部保留
    """
    overview = data.get("overview")
    if isinstance(overview, dict):
        overview.pop("markdown", None)
    components = data.get("components") or {}
    for it in components.get("items") or []:
        source = it.get("source") or {}
        files = source.get("files") or []
        source["files"] = [
            OrderedDict([("lang", f.get("lang")), ("path", f.get("path"))])
            for f in files
            if f.get("lang") == "html"
        ]
    patterns = data.get("patterns") or {}
    for card in (patterns.get("view") or {}).get("cards") or []:
        for state in (card.get("states") or {}).values():
            if isinstance(state, dict):
                state.pop("html", None)
