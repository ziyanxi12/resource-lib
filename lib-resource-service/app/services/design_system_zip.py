"""设计系统六部件解析服务（octo-design-parts/1 格式）。

六部件（multipart 各自独立上传、独立成败，失败部件忽略并回报错误）：
    design_md    DESIGN.md 原文：UTF-8 校验后原样存 {slug}/source.md
                 （json.overview 存其相对路径，展示端 fetch 后 markdown 渲染）
    tokens       tokens.json（唯一数据源）：UTF-8 + JSON 校验 → 原件存 {slug}/tokens.json；
                 v4.4 起不再做 legacy 转换——design-system.json 的 color/typography/
                 spacing/radius/shadow/other 六键从原件顶层原样深拷贝
    components   组件 zip：根须含 components/ 目录；落盘 {slug}/assets/components/**，
                 条目扫描见 scan_group_items（spec.json 优先，老结构按叶子 html）
    patterns     Pattern zip：根须含 patterns/ 目录，同组件包规则，
                 落盘 {slug}/assets/patterns/**
    skill        skill 包 zip：第一层须含 SKILL.md（frontmatter name 非空 → 加
                 design-system- 前缀改写，v4.3），改写后落盘 {slug}/{原文件名}
    preview      预览页面包 zip：整站落盘 {slug}/preview/**，入口 html 记 preview_entry_path

components/patterns zip 兼容同名双层嵌套（components/components/…）：
locate_group_base 循环剥离同名子层后以最内层为基目录。

职责：
- 安全校验：zip slip（`..`/绝对路径/反斜杠/symlink）、zip bomb（条目数/解压总大小/
  压缩比）、同名冲突条目（目录/文件同名及大小写变体）
- 打包垃圾静默丢弃：macOS/Windows 压缩工具产物（__MACOSX/、._* AppleDouble、
  .DS_Store、Thumbs.db，含嵌套路径）不报错、不落盘、不参与解析——用户本机
  「右键压缩」产生的 zip 必然携带，属正常现象而非非法内容
- 解压到临时目录（zip 字节先写临时文件再解压，对齐需求「先落盘，再解压」）
- 各部件独立校验 / 解析原语（本模块不落盘到 {slug}/，正式入库走
  design_system_service.import_parts 编排）
- skill 包严格校验：第一层 SKILL.md + frontmatter name 非空 ≤255 字符（含前缀）

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
MAX_SKILL_NAME_LEN = 255                    # SKILL.md frontmatter name 最终长度上限（含前缀，对齐 DB 列宽）
SKILL_NAME_PREFIX = "design-system-"        # v4.3：skill 名统一前缀（ingest 时改写 SKILL.md 的 name）

# skill 包落盘时不得与 design-systems/{slug}/ 下的系统保留文件重名（大小写不敏感）
RESERVED_SKILL_NAMES = {"source.zip", "source.md", "design-system.json", "tokens.json", "preview"}

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

def parse_tokens_bytes(content: bytes) -> Dict:
    """tokens.json 部件校验：UTF-8（容忍 BOM）+ 合法 JSON + 顶层对象 → 返回原件 dict。

    **唯一数据源**：JSON 语法错误是硬错误 → ZipPackageError；分组结构零校验
    （color/… 缺失 → 模板渲染空态）。v4.4 起不再做 legacy 转换——
    design-system.json 六个 token 键从原件顶层原样深拷贝（见 service.rebuild_design_system_json）。
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
    return raw


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


def _uniquify_ids(items: List[Dict]) -> None:
    """不同目录同名条目：id 追加序号保证唯一（name 保留原名）。"""
    seen: Dict[str, int] = {}
    for it in items:
        base_id = re.sub(r"[^a-z0-9-]", "-", str(it["name"]).lower()).strip("-") or "comp"
        seen[base_id] = seen.get(base_id, 0) + 1
        it["id"] = base_id if seen[base_id] == 1 else "%s-%d" % (base_id, seen[base_id])


def scan_group_items(group_root: str, group: str) -> List[Dict]:
    """扫描 assets/{group} 子树 → design-system.json 条目（v4.4：{id, name, group, height, html}）。

    条目来源（落盘现状扫描，index.json 有则按其 items 顺序）：
    - **spec.json 优先**（v3/v4 转化产物）：目录含 spec.json = 一个条目——
      name = spec.name、html = spec.preview.file（spec 目录内相对路径，文件须存在；
      preview 缺失/文件不存在 → 该条目不上网站，整目录跳过不回退——combos 等辅助
      html 不应被误当成独立条目）
    - **无 spec.json 的目录**（老 zip 结构）：叶子 html 逐个成条（历史规则——
      目录层级 = group、文件名去扩展 = name）
    - html 为 design-systems/{slug}/ 起的 POSIX 相对路径（含 assets/{group}/ 前缀），
      模板按 jsonUrl 目录解析
    - spec.json 读取失败（非法 JSON）→ 该目录按无 spec 的老规则扫 html（容错不中断）
    """
    items = []
    if not os.path.isdir(group_root):
        return items
    prefix = "assets/%s/" % group
    spec_dirs = set()

    def rel_levels(dirpath):
        rel = os.path.relpath(dirpath, group_root).replace(os.sep, "/")
        return [x for x in rel.split("/") if x not in (".", "")]

    # ① spec.json 目录 → 条目（整目录子树由 spec 拥有，其中的其他 html 不再单独成条）
    for dirpath, dirnames, filenames in os.walk(group_root):
        if "spec.json" not in filenames:
            continue
        spec_path = os.path.join(dirpath, "spec.json")
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
            if not isinstance(spec, dict):
                raise ValueError("顶层不是对象")
        except (ValueError, OSError) as e:
            logger.warning("[scan] %s spec.json 读取失败，目录按老结构扫 html：%s", spec_path, e)
            continue
        spec_dirs.add(dirpath)
        levels = rel_levels(dirpath)
        name = str(spec.get("name") or "").strip() or levels[-1]
        # 分类：spec.group 优先（转化产物已给分类）；缺省回落目录层级去组件目录本身（["通用类","Button"]→["通用类"]）
        sg = spec.get("group")
        if isinstance(sg, list) and sg:
            group = [str(x) for x in sg if str(x).strip()]
        elif isinstance(sg, str) and sg.strip():
            group = [sg.strip()]
        else:
            group = levels[:-1] if len(levels) > 1 else []
        pf = str((spec.get("preview") or {}).get("file") or "").strip()
        if not pf or pf.startswith(("/", "..")):
            continue  # 没有 preview 的条目不上网站
        html_abs = os.path.normpath(os.path.join(dirpath, pf))
        # dirpath 可能带 ./ 前缀（相对 FILE_ROOT_DIR 配置），normpath 归一后再比较
        if not (os.path.isfile(html_abs) and os.path.commonpath([os.path.normpath(dirpath), html_abs]) == os.path.normpath(dirpath)):
            continue
        rel_dir = "/".join(levels)
        items.append({
            "name": name,
            "group": group,
            "html": prefix + rel_dir + "/" + pf.replace(os.sep, "/"),
            "_order_key": rel_dir + "/spec.json",  # index.json items 的形态（无 assets 前缀）
        })

    # ② 无 spec.json 的目录（老 zip 结构）：叶子 html 逐个成条（spec 目录子树跳过）
    for dirpath, dirnames, filenames in os.walk(group_root):
        if any(d == dirpath or dirpath.startswith(d + os.sep) for d in spec_dirs):
            dirnames[:] = []
            continue
        levels = rel_levels(dirpath)
        for fn in sorted(filenames):
            if _is_junk_entry(fn) or not fn.lower().endswith(".html"):
                continue
            rel_html = "/".join(levels + [fn])
            items.append({
                "name": fn[:-len(".html")],
                "group": levels,
                "html": prefix + rel_html,
                "_order_key": rel_html,
            })

    # ③ 排序：index.json 的 items 顺序优先（转化 skill 定义的展示顺序），其余按路径稳定排序
    try:
        with open(os.path.join(group_root, "index.json"), "r", encoding="utf-8") as f:
            idx = json.load(f)
        order = {str(p): i for i, p in enumerate((idx or {}).get("items") or [])}
    except (ValueError, OSError):
        order = {}
    if order:
        items.sort(key=lambda it: (order.get(it.pop("_order_key", ""), len(order)), it["html"]))
    else:
        for it in items:
            it.pop("_order_key", None)
        items.sort(key=lambda it: it["html"])

    _uniquify_ids(items)
    return [
        OrderedDict([
            ("id", it["id"]),
            ("name", it["name"]),
            ("group", it["group"]),
            ("height", DEFAULT_ROW_HEIGHT),
            ("html", it["html"]),
        ])
        for it in items
    ]


def ingest_group_zip(content: bytes, group: str, dst_group_dir: str) -> Dict:
    """组件包 / Pattern 包部件导入：校验 + 解压 + 定位（含同名嵌套剥离）+ 落盘。

    - 安全校验同上传入口（validate_zip_bytes：slip/bomb/条目数/同名冲突）
    - zip 根须含 {group}/ 目录（否则该部件失败）；同名嵌套层（components/components/）
      循环剥离后以最内层为基目录
    - 落盘：dst_group_dir（= design-systems/{slug}/assets/{group}）整体替换——
      先清空旧子树再拷入新内容；本函数任何一步抛错时目标子树不受影响
    - v4.4：不再构建 json 区块——落盘后由 service.rebuild_design_system_json
      从落盘现状全量扫描条目（scan_group_items）；条目计数一并由重建结果回报
    - 返回 {"nested": 是否剥离}
    """
    label = GROUP_LABEL.get(group, group)
    validate_zip_bytes(content)
    with tempfile.TemporaryDirectory(prefix="ds-group-") as tmp:
        extract_zip(content, tmp)
        base, nested = locate_group_base(tmp, group)
        # 落盘：先验证后拷贝（copytree 失败属于系统级异常，不属于部件校验失败）
        if os.path.isdir(dst_group_dir):
            shutil.rmtree(dst_group_dir)
        os.makedirs(os.path.dirname(dst_group_dir), exist_ok=True)
        shutil.copytree(base, dst_group_dir)
        logger.info("[parts-import] %s包落盘完成：%s",
                    label, "检测到同名嵌套目录并已剥离" if nested else "标准结构")
        return {"nested": nested}


# ─────────────────────────── 部件 6：预览页面包 ───────────────────────────

def _locate_preview_base(extract_root: str) -> Tuple[str, bool]:
    """定位预览页扫描基目录，返回 (基目录绝对路径, 是否发生包裹剥离)。

    - zip 根直接含 html 文件 → 根即基目录（标准结构）
    - 根无 html 且只有一个目录条目（右键压缩产物的单层包裹，目录名任意）→ 向内剥离，
      循环最多 3 层防多层套娃；剥离后仍无 html → ZipPackageError
    """
    base = extract_root
    nested = False
    for _ in range(3):
        entries = [e for e in os.listdir(base) if not _is_junk_entry(e)]
        has_html = any(e.lower().endswith(".html") and os.path.isfile(os.path.join(base, e)) for e in entries)
        if has_html:
            return base, nested
        dirs = [e for e in entries if os.path.isdir(os.path.join(base, e))]
        if len(dirs) == 1:
            nested = True
            base = os.path.join(base, dirs[0])
            logger.warning("[parts-import] 预览页面包检测到单层包裹目录，向内剥离一层（当前基目录：%s）", base)
            continue
        raise ZipPackageError("预览页面包 zip 里没有 html 文件（入口按根下 index.html 识别）")
    raise ZipPackageError("预览页面包 zip 包裹目录层级过深（超过 3 层）或内层没有 html 文件")


def _resolve_preview_entry(base: str) -> str:
    """解析预览页入口 html 文件名：index.html 优先；否则根下唯一 .html 兜底；无/多个 → 部件失败。"""
    htmls = sorted(
        e for e in os.listdir(base)
        if e.lower().endswith(".html") and os.path.isfile(os.path.join(base, e)) and not _is_junk_entry(e)
    )
    if not htmls:
        raise ZipPackageError("预览页面包 zip 里没有 html 文件（入口按根下 index.html 识别）")
    if "index.html" in htmls or "index.HTML" in htmls or "Index.html" in htmls:
        for h in htmls:
            if h.lower() == "index.html":
                return h
    if len(htmls) == 1:
        logger.warning("[parts-import] 预览页面包根下无 index.html，使用唯一 html 作为入口：%s", htmls[0])
        return htmls[0]
    raise ZipPackageError(
        "预览页面包根下有多个 html（%s）且没有 index.html，无法确定入口" % " / ".join(htmls[:5]))


def ingest_preview_zip(content: bytes, dst_preview_dir: str) -> Dict:
    """预览页面包部件导入：校验 + 解压 + 包裹剥离 + 入口解析 + 整包落盘。

    - 安全校验同上传入口（validate_zip_bytes：slip/bomb/条目数/同名冲突）
    - 基目录定位（_locate_preview_base）：根含 html 即标准；单层任意名包裹自动剥离
    - 入口解析（_resolve_preview_entry）：index.html 优先 → 根下唯一 .html 兜底
    - 落盘：dst_preview_dir（= design-systems/{slug}/preview）整体替换——
      先清空旧子树再拷入新内容；本函数任何一步抛错时目标子树不受影响
    - 返回 {"entry": 入口 html 文件名（preview_url 指向它）, "nested": 是否剥离}
    """
    validate_zip_bytes(content)
    with tempfile.TemporaryDirectory(prefix="ds-preview-") as tmp:
        extract_zip(content, tmp)
        base, nested = _locate_preview_base(tmp)
        entry = _resolve_preview_entry(base)
        if os.path.isdir(dst_preview_dir):
            shutil.rmtree(dst_preview_dir)
        os.makedirs(os.path.dirname(dst_preview_dir), exist_ok=True)
        shutil.copytree(base, dst_preview_dir)
        logger.info("[parts-import] 预览页面包导入完成：入口 %s，%s",
                    entry, "检测到包裹目录并已剥离" if nested else "标准结构")
        return {"entry": entry, "nested": nested}


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


def ingest_skill_zip_bytes(content: bytes) -> Tuple[str, bytes]:
    """skill 包部件 ingest（v4.3：name 加 design-system- 前缀改写）。

    zip 字节 → (改写后技能名, 改写后 zip 字节)。失败抛 ZipPackageError（该部件失败）。

    - 校验同 parse_skill_zip_bytes（zip 合法 / 第一层 SKILL.md / frontmatter name 非空）
    - name 改写：非 ``design-system-`` 开头 → ``design-system-{name}``；已带前缀原样（幂等，
      重复上传已处理包不会双重前缀）；最终名（含前缀）> MAX_SKILL_NAME_LEN → 该部件失败
    - zip 重建：SKILL.md 条目替换为改写后内容（仅 frontmatter 块内首个 ``name:`` 行，
      frontmatter 外的正文不动），其余条目原字节保留、条目顺序不变
    """
    raw_name = parse_skill_zip_bytes(content)
    final_name = raw_name if raw_name.startswith(SKILL_NAME_PREFIX) else SKILL_NAME_PREFIX + raw_name
    if len(final_name) > MAX_SKILL_NAME_LEN:
        raise ZipPackageError(
            "skill 名加前缀后超过 %d 字符（原名 %d 字符）" % (MAX_SKILL_NAME_LEN, len(raw_name)))
    if final_name == raw_name:
        # 已带前缀（幂等命中）：无需重建 zip，原字节落盘
        return final_name, content
    return final_name, _rewrite_skill_md_name(content, final_name)


def _rewrite_skill_md_name(content: bytes, new_name: str) -> bytes:
    """重建 skill zip：SKILL.md 的 frontmatter name 行替换为 new_name，其余条目原样。

    只改 frontmatter（--- ... ---）块内第一个 ``name:`` 行；正文里的 name: 行不动。
    输出条目顺序与原包一致，压缩统一 deflate。
    """
    src = zipfile.ZipFile(io.BytesIO(content))
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info in src.infolist():
            data = src.read(info)
            if info.filename == "SKILL.md":
                text = data.decode("utf-8")
                text = _replace_frontmatter_name(text, new_name)
                data = text.encode("utf-8")
            out.writestr(info, data)
    src.close()
    return out_buf.getvalue()


def _replace_frontmatter_name(text: str, new_name: str) -> str:
    """SKILL.md 文本 frontmatter 块内首个 name: 行替换（无 frontmatter/无 name 行时原样返回——
    上游 ingest_skill_zip_bytes 已校验存在，此处仅防御）。"""
    m = re.match(r"^---\s*\n", text)
    if not m:
        return text
    end = text.find("\n---", m.end())
    if end == -1:
        return text
    head, body = text[:end], text[end:]
    replaced = re.sub(r"(?m)^(\s*)name:\s*.*$", lambda mo: "%sname: %s" % (mo.group(1), new_name), head, count=1)
    return replaced + body
