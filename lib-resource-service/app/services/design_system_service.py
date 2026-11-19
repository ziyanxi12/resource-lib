"""设计系统业务逻辑：五部件导入、卡片 meta 派生、作者/封面/图标、文件存储。

校验与语义严格对齐 requirement/api.md 契约（octo-design-parts/1 五部件格式）：
- 上传物为五个独立部件（multipart 各自可选、独立成败，失败部件忽略并回报错误）：
  DESIGN.md（UTF-8 → source.md）/ tokens.json（唯一数据源 → token 区块 + 原件落盘）/
  组件包 zip（components/ 目录）/ Pattern 包 zip（patterns/ 目录）/ skill 包 zip
  （第一层 SKILL.md）；组件/Pattern 包兼容同名多层嵌套（components/components/…）
- slug 由后端生成（8 位随机 [a-z0-9]）：API 路径 / 落盘目录 / 静态 URL；
  tokens.json 的 id 原样保留在 source_slug（不唯一，允许重复）
- name 必填（表单；tokens.name 为历史兼容回落）；usage 不从任何文件派生：
  新增恒 0，修正通道仅表单 usage 字段；部件替换保留现值
- author 为对象数组 [{account, nick_name, dept}]，写入时经 users 表补全昵称/部门（固化存储）；
  旧字符串数据读取时自动包装为单元素数组（无需迁移）
- cover 不在内置封面集时回落默认（不报错）；icon 支持自定义上传（jpg/png/webp/svg）
- 部件替换（PUT /{slug}/parts）：只换提供部件的内容（token 区块 / assets 子树 / 附件），
  name/source_slug 等管理字段不跟随（meta 走 PATCH）；老系统无 tokens 原件时
  按 json 存量 token 区块保留（未提供 tokens 部件则完全不动）
"""

import json
import logging
import os
import re
import secrets
import shutil
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services import design_system_zip as dzip

logger = logging.getLogger(__name__)

BUILTIN_COVERS = ["cover-blue.jpg", "cover-cyan.jpg", "cover-purple.jpg", "cover-violet.jpg"]
DEFAULT_COVER = "cover-cyan.jpg"
MAX_COVER_BYTES = 2 * 1024 * 1024
ALLOWED_COVER_EXTS = {"jpg", "jpeg", "png", "webp"}
COVERS_REL_DIR = "design-systems/covers"
MAX_ICON_BYTES = 2 * 1024 * 1024
ALLOWED_ICON_EXTS = {"jpg", "jpeg", "png", "webp", "svg"}
ICONS_REL_DIR = "design-systems/icons"

# slug 随机生成（后端分配，与文件内容解耦）：8 位 [a-z0-9] ≈ 2.8e12 组合
SLUG_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
SLUG_LENGTH = 8

# ─────────────────────────── 五部件 ───────────────────────────

# 部件名（multipart 字段去 _file 后缀）
PART_FIELDS = ("design_md", "tokens", "components", "patterns", "skill", "preview")

# token 区块标准键（legacy 转换产物；老系统无 tokens 原件时按此剔除旧区块）
TOKEN_SECTION_KEYS = ("color", "typography", "spacing", "radius", "shadow")

# design-system.json 的 token 六键（v4.4：从 tokens.json 原件顶层原样深拷贝进 json，
# other 供模板 LIVE token 注入消费——描边等不在八栏里的 token）
TOKEN_JSON_KEYS = ("color", "typography", "spacing", "radius", "shadow", "other")


def normalize_cover(cover) -> str:
    """JSON 派生/表单传入的 cover：仅认内置封面名，其余回落默认（不报错）。"""
    return cover if isinstance(cover, str) and cover in BUILTIN_COVERS else DEFAULT_COVER


def _is_custom_cover(val) -> bool:
    """自定义封面以完整相对路径存储（design-systems/covers/{slug}.{ext}）。"""
    return isinstance(val, str) and val.startswith(COVERS_REL_DIR + "/")


def resolve_cover(cover) -> str:
    """解析存储/输入的 cover 值：自定义相对路径原样透传；内置名校验；其余回落默认。"""
    if not cover:
        return DEFAULT_COVER
    s = cover if isinstance(cover, str) else str(cover)
    if _is_custom_cover(s):
        return s
    if s in BUILTIN_COVERS:
        return s
    return DEFAULT_COVER


def extract_meta(data: dict) -> dict:
    """从 JSON 派生卡片 meta（管理字段默认值，可被表单覆盖）。

    注意：usage 不从 tokens.json 派生（需求明确：md 里的 usage 不允许直接使用）。
    新增系统恒 0 起步；修正通道仅表单 usage 字段（手动）与 /usage 自增接口。
    """
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "source_slug": str(data.get("id") or ""),
        "name": str(data.get("name") or ""),
        "desc": meta.get("desc") if isinstance(meta.get("desc"), str) else "",
        "author": meta.get("author") if isinstance(meta.get("author"), str) else "",
        "cover": normalize_cover(data.get("cover")),
        "default": False,
    }


def rel_path(slug: str) -> str:
    """JSON 文件相对 FILE_ROOT_DIR 的路径"""
    return "design-systems/%s/design-system.json" % slug


def abs_path(slug: str) -> str:
    return os.path.join(settings.FILE_ROOT_DIR, rel_path(slug))


def save_json_file(slug: str, data: dict, file_size: int = 0) -> None:
    """写入 JSON 文件到 FILE_ROOT_DIR/design-systems/{slug}/design-system.json"""
    path = abs_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    _ = file_size  # 尺寸由调用方记录到 DB（现按 {slug} 目录落盘内容合计重算）


def _read_json_file(slug: str) -> dict:
    """读取存量 design-system.json（替换模式合并基线）；缺失/损坏回落空 dict。"""
    path = abs_path(slug)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError) as e:
        logger.warning("[parts-import] 存量 design-system.json 读取失败（按空基线合并）：%s", e)
        return {}


def _dir_size(slug: str) -> int:
    """{slug} 目录落盘内容合计（design-system.json / source.md / tokens.json /
    assets/** / skill 包——file_size 列的取值口径）。"""
    root = os.path.join(settings.FILE_ROOT_DIR, "design-systems", slug)
    total = 0
    if not os.path.isdir(root):
        return total
    for _dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            try:
                total += os.path.getsize(os.path.join(root, fn))
            except OSError:
                continue
    return total


def delete_json_file(slug: str) -> None:
    """软删场景下保留文件，仅清理 DB 记录；物理删除留给回收站/清理任务"""
    return


def _to_public_url(rel_path: str) -> str:
    """相对路径 → 完整可访问 URL（对齐 resources.py 同名逻辑）。

    - 已是 http(s):// 完整 URL 则原样返回
    - PUBLIC_ORIGIN 非空：{PUBLIC_ORIGIN}{ROOT_PATH}/static/{path}（生产填真实域名 + ROOT_PATH=/aaa）
    - PUBLIC_ORIGIN 为空：ROOT_PATH 相对路径（由前端代理）
    """
    if re.match(r"^(https?:)?//", rel_path, re.I):
        return rel_path
    if settings.PUBLIC_ORIGIN:
        return "%s%s/static/%s" % (settings.PUBLIC_ORIGIN.rstrip("/"), settings.ROOT_PATH, rel_path)
    return "%s/static/%s" % (settings.ROOT_PATH, rel_path)


def cover_url(cover: Optional[str]) -> str:
    """封面完整 URL（兼容内置名与自定义相对路径两种）。"""
    resolved = resolve_cover(cover)
    rel = resolved if _is_custom_cover(resolved) else "%s/%s" % (COVERS_REL_DIR, resolved)
    return _to_public_url(rel)


def json_url(file_path: str) -> str:
    """design-system.json 完整 URL（展示端详情数据源）"""
    return _to_public_url(file_path)


def resolve_display_map(db, accounts) -> dict:
    """account → "昵称 account" 显示字符串。

    直查 users 表（AuthMiddleware 每次请求 upsert），查不到回落原样；
    不复用 user_service.resolve_display_names——它会对未知账号调外部 API 补查，seed/unknown 会卡。
    """
    unique = {a for a in accounts if a}
    if not unique:
        return {}
    try:
        from app.models.user import User

        rows = db.query(User.account, User.nick_name).filter(User.account.in_(unique)).all()
        return {acc: ("%s %s" % (nick, acc) if nick else acc) for acc, nick in rows}
    except Exception:  # noqa: BLE001
        return {}


def parse_form_bool(val) -> Optional[bool]:
    """multipart/表单里的布尔字段："true"/"false"（大小写不敏感）→ bool；空 → None"""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s == "true":
        return True
    if s == "false":
        return False
    return None


def parse_form_int(val, label="调用量") -> Optional[int]:
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(str(val).strip())
    except ValueError:
        raise ValueError("%s必须为整数，收到：%s" % (label, val))


# ─────────────────────────── 部件落盘路径 ───────────────────────────

def _slug_dir(slug: str) -> str:
    return os.path.join(settings.FILE_ROOT_DIR, "design-systems", slug)


def source_md_rel_path(slug: str) -> str:
    """DESIGN.md 原件相对 FILE_ROOT_DIR 的路径（固定命名；design_md 部件落盘件）"""
    return "design-systems/%s/source.md" % slug


def tokens_rel_path(slug: str) -> str:
    """tokens.json 原件相对 FILE_ROOT_DIR 的路径（tokens 部件落盘件）"""
    return "design-systems/%s/tokens.json" % slug


def skill_zip_rel_path(slug: str, orig_name: str) -> str:
    """skill 包相对路径（驱动 skill_zip_url 下载）：保留上传原文件名"""
    return "design-systems/%s/%s" % (slug, os.path.basename(orig_name))


def group_dir(slug: str, group: str) -> str:
    """组件/Pattern 包落盘目录（{slug}/assets/{group}；html 等经 /static 可直接访问）"""
    return os.path.join(_slug_dir(slug), "assets", group)


def preview_dir(slug: str) -> str:
    """预览页面包落盘目录（{slug}/preview；整站经 /static 可直接访问）"""
    return os.path.join(_slug_dir(slug), "preview")


def preview_entry_rel_path(slug: str, entry: str) -> str:
    """预览页入口 html 相对 FILE_ROOT_DIR 的路径（驱动 preview_url；存 DB preview_entry_path 列）"""
    return "design-systems/%s/preview/%s" % (slug, os.path.basename(entry))


def save_source_md(slug: str, content: bytes) -> str:
    """保存 DESIGN.md 原件到 design-systems/{slug}/source.md，返回相对路径（存 DB source_md_path 列）。"""
    path = os.path.join(settings.FILE_ROOT_DIR, source_md_rel_path(slug))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return source_md_rel_path(slug)


def save_tokens_file(slug: str, content: bytes) -> str:
    """保存 tokens.json 原件到 design-systems/{slug}/tokens.json，返回相对路径。"""
    rel = tokens_rel_path(slug)
    path = os.path.join(settings.FILE_ROOT_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return rel


def save_part_file(slug: str, orig_name: str, content: bytes) -> str:
    """skill 包原样落盘到 design-systems/{slug}/{原文件名}（不解析，保留原名）。"""
    rel = skill_zip_rel_path(slug, orig_name)
    path = os.path.join(settings.FILE_ROOT_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return rel


def remove_skill_zip(rel_path: Optional[str]) -> None:
    """按 DB 列记录的相对路径删除旧 skill 包。

    部件替换时新包名可能与旧的不同（保留原文件名），固定路径「覆盖」不到旧文件，
    故按 skill_zip_path 列的路径清理；同名时无需调用（write 已覆盖）。
    """
    if not rel_path:
        return
    path = os.path.join(settings.FILE_ROOT_DIR, rel_path)
    if os.path.isfile(path):
        os.remove(path)


# ─────────────────────────── 六部件导入（新增 / 替换共用编排） ───────────────────────────

def _read_tokens_raw(slug: str) -> Optional[dict]:
    """读 {slug}/tokens.json 原件（容忍 BOM）；不存在/损坏返回 None。"""
    path = os.path.join(settings.FILE_ROOT_DIR, tokens_rel_path(slug))
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            raw = json.loads(f.read().decode("utf-8-sig"))
        return raw if isinstance(raw, dict) else None
    except (ValueError, UnicodeDecodeError, OSError):
        return None


def rebuild_design_system_json(slug: str, old_data: Optional[dict] = None) -> Tuple[dict, dict]:
    """从 {slug} 落盘现状全量重建 design-system.json（v4.4：8+1 键单数据源）。

    结构（模板唯一数据源，jsonUrl 直连消费）：
    - ``overview``：恒 "source.md"（design_md 部件落盘件相对路径；文件不存在时
      模板 fetch 404 → 概览栏容错提示）
    - ``color/typography/spacing/radius/shadow/other``：**tokens.json 原件顶层同名键
      原样深拷贝**；原件缺失的键回落 old json 同名键（老系统无原件 → 转换产物兼容；
      原件缺失且老 json 也没有 → 不写该键，模板栏级容错空态）
    - ``components/patterns``：scan_group_items 扫 assets/{group} 子树出条目
      {id, name, group, height, html}；无条目不写该键（模板空态）
    - 其余顶层键（老结构的 name/meta/coverage/source.files 内嵌源码等）一律不再写入

    返回 (data, counts)，counts = {"components": 条目数, "patterns": 条目数}。
    """
    if not isinstance(old_data, dict):
        old_data = _read_json_file(slug)
    data = OrderedDict()
    data["overview"] = "source.md"
    raw = _read_tokens_raw(slug)
    for k in TOKEN_JSON_KEYS:
        if raw is not None and k in raw:
            data[k] = raw[k]
        elif k in old_data:
            data[k] = old_data[k]
    counts = {}
    for part in ("components", "patterns"):
        items = dzip.scan_group_items(group_dir(slug, part), part)
        counts[part] = len(items)
        if items:
            data[part] = OrderedDict([("items", items)])
    return data, counts


def import_parts(
    db,
    part_files: Dict[str, Tuple[str, bytes]],
    existing=None,
) -> dict:
    """六部件导入主流程（POST 新增与 PUT /{slug}/parts 替换共用）。

    - 逐部件独立成败：任一部件校验/解析失败 → 该部件忽略并记入 ingest 报告
      （{"provided", "ok", "error"/"count"/"skill_name"}），其余部件正常入库
    - part_files：{部件名: (文件名, 字节)}，仅包含请求里实际提供了的部件
    - v4.4 组装方式：逐部件落盘后从 {slug} 落盘现状**全量重建** design-system.json
      （rebuild_design_system_json——未提供部件的落盘件未动，天然保留存量）
    - 返回 {"data": json dict, "slug", "tokens_raw"（tokens 部件原件，未提供为 None）,
      "source_slug", "source_md_rel"/"tokens_rel"/"skill_zip_rel"/"skill_name"
      （仅部件成功提供时非 None）, "ingest": 报告, "file_size": 目录合计}
    """
    is_create = existing is None
    slug = existing.slug if existing is not None else generate_slug(db)
    logger.info("[parts-import] 开始导入：%s，部件：%s",
                "重传 slug=%s" % slug if not is_create else "新增",
                "、".join(k for k in PART_FIELDS if k in part_files) or "（空）")

    report = {f: {"provided": f in part_files} for f in PART_FIELDS}
    old_data = {} if is_create else _read_json_file(slug)

    source_md_rel = None
    tokens_rel = None
    skill_zip_rel = None
    skill_name = None
    preview_entry_rel = None
    tokens_raw = None

    # ① DESIGN.md：UTF-8 校验 → source.md 落盘
    if "design_md" in part_files:
        _fname, content = part_files["design_md"]
        try:
            dzip.parse_design_md_bytes(content)
            source_md_rel = save_source_md(slug, content)
            report["design_md"] = {"provided": True, "ok": True, "size": len(content)}
        except (dzip.ZipPackageError, ValueError) as e:
            report["design_md"] = {"provided": True, "ok": False, "error": str(e)}

    # ② tokens.json：JSON 校验 → 原件落盘（v4.4：不做转换，json 六键重建时原样深拷贝）
    if "tokens" in part_files:
        _fname, content = part_files["tokens"]
        try:
            tokens_raw = dzip.parse_tokens_bytes(content)
            tokens_rel = save_tokens_file(slug, content)
            report["tokens"] = {"provided": True, "ok": True, "size": len(content)}
        except (dzip.ZipPackageError, ValueError) as e:
            report["tokens"] = {"provided": True, "ok": False, "error": str(e)}

    # ③④ 组件包 / Pattern 包：安全解压 → 定位（同名嵌套剥离）→ assets/{group} 子树整体替换
    for part in ("components", "patterns"):
        if part not in part_files:
            continue
        _fname, content = part_files[part]
        try:
            ingested = dzip.ingest_group_zip(content, part, group_dir(slug, part))
            entry = {"provided": True, "ok": True}
            if ingested["nested"]:
                entry["nested"] = True
            report[part] = entry
        except (dzip.ZipPackageError, ValueError) as e:
            report[part] = {"provided": True, "ok": False, "error": str(e)}

    # ⑤ skill 包：保留名校验 + SKILL.md/frontmatter name 校验 + v4.3 前缀改写 → 落盘（改写后版本）
    if "skill" in part_files:
        fname, content = part_files["skill"]
        try:
            orig = os.path.basename(fname or "skill.zip")
            if orig.lower() in dzip.RESERVED_SKILL_NAMES:
                raise dzip.ZipPackageError(
                    "skill 包文件名「%s」与系统保留文件（%s）冲突，请重命名后重新上传"
                    % (orig, " / ".join(sorted(dzip.RESERVED_SKILL_NAMES))))
            # v4.3：name 非 design-system- 开头 → 改写（幂等）；落盘 zip 内 SKILL.md 为改写后版本
            skill_name, skill_content = dzip.ingest_skill_zip_bytes(content)
            skill_zip_rel = save_part_file(slug, orig, skill_content)
            # 旧附件清理放在新包落盘成功之后（此前任何失败都不破坏现有文件）
            if existing is not None and existing.skill_zip_path and existing.skill_zip_path != skill_zip_rel:
                remove_skill_zip(existing.skill_zip_path)
            report["skill"] = {"provided": True, "ok": True, "skill_name": skill_name, "size": len(skill_content)}
        except (dzip.ZipPackageError, ValueError) as e:
            report["skill"] = {"provided": True, "ok": False, "error": str(e)}

    # ⑥ 预览页面包：安全解压 + 单层包裹剥离 + 入口解析 → preview/ 子树整体替换
    if "preview" in part_files:
        _fname, content = part_files["preview"]
        try:
            ingested = dzip.ingest_preview_zip(content, preview_dir(slug))
            preview_entry_rel = preview_entry_rel_path(slug, ingested["entry"])
            entry = {"provided": True, "ok": True, "entry": ingested["entry"], "size": len(content)}
            if ingested["nested"]:
                entry["nested"] = True
            report["preview"] = entry
        except (dzip.ZipPackageError, ValueError) as e:
            report["preview"] = {"provided": True, "ok": False, "error": str(e)}

    # 组装收尾（v4.4）：从 {slug} 落盘现状全量重建 design-system.json（8+1 键单数据源）
    data, counts = rebuild_design_system_json(slug, old_data)
    # ingest 报告回填条目计数（重建扫出的真实条目数）
    for part in ("components", "patterns"):
        if report[part].get("provided") and report[part].get("ok"):
            report[part]["count"] = counts[part]
    save_json_file(slug, data)
    file_size = _dir_size(slug)

    # source_slug：tokens 原件 id 优先（v4 原件可缺失 → 替换模式沿用存量 id → slug 兜底）
    raw_id = str((tokens_raw or {}).get("id") or "").strip() if tokens_raw else ""
    if raw_id:
        source_slug = raw_id
    elif is_create:
        source_slug = slug
    else:
        source_slug = str((old_data or {}).get("id") or "").strip() or slug

    failed = [f for f in PART_FIELDS if report[f].get("provided") and not report[f].get("ok")]
    logger.info(
        "[parts-import] 落盘完成：slug=%s source_slug=%s skill_name=%s；json=%dB 目录合计=%dB；"
        "部件成败：%s%s",
        slug, source_slug, skill_name,
        os.path.getsize(abs_path(slug)), file_size,
        "、".join("%s=%s" % (f, "ok" if report[f].get("ok") or not report[f].get("provided") else "失败")
                  for f in PART_FIELDS),
        "（失败：%s）" % "、".join(failed) if failed else "",
    )
    return {
        "data": data,
        "slug": slug,
        "tokens_raw": tokens_raw,
        "source_slug": source_slug,
        "source_md_rel": source_md_rel,
        "tokens_rel": tokens_rel,
        "skill_zip_rel": skill_zip_rel,
        "skill_name": skill_name,
        "preview_entry_rel": preview_entry_rel,
        "ingest": report,
        "file_size": file_size,
    }


# ─────────────────────────── 列表条目 / parts 存在性 ───────────────────────────

def _tokens_url(row) -> Optional[str]:
    """tokens.json 原件下载 URL（部件落盘件存在才返回；老系统无原件为 None）。"""
    rel = tokens_rel_path(row.slug)
    if os.path.isfile(os.path.join(settings.FILE_ROOT_DIR, rel)):
        return _to_public_url(rel)
    return None


def compute_parts(row) -> dict:
    """item.parts 存在性（管理台编辑/查看用；展示端忽略）。

    - design_md：source.md 落盘件存在（老系统同样有 source.md）
    - tokens：tokens.json 原件存在，或 json 含 token 区块（老系统按数据判断）
    - components/patterns：json 区块存在且有 items（含计数）
    - skill：skill_zip_path 列非空且落盘件存在
    - preview：preview_entry_path 列非空且落盘件存在
    """
    parts = {
        "design_md": False,
        "tokens": False,
        "components": False,
        "patterns": False,
        "skill": False,
        "preview": False,
        "components_count": 0,
        "patterns_count": 0,
    }
    try:
        if row.source_md_path and os.path.isfile(os.path.join(settings.FILE_ROOT_DIR, row.source_md_path)):
            parts["design_md"] = True
        if row.skill_zip_path and os.path.isfile(os.path.join(settings.FILE_ROOT_DIR, row.skill_zip_path)):
            parts["skill"] = True
        if row.preview_entry_path and os.path.isfile(os.path.join(settings.FILE_ROOT_DIR, row.preview_entry_path)):
            parts["preview"] = True
        if os.path.isfile(os.path.join(settings.FILE_ROOT_DIR, tokens_rel_path(row.slug))):
            parts["tokens"] = True
        data = _read_json_file(row.slug)
        if data:
            comp_items = (data.get("components") or {}).get("items") or []
            pat_items = (data.get("patterns") or {}).get("items") or []
            parts["components"] = bool(comp_items)
            parts["patterns"] = bool(pat_items)
            parts["components_count"] = len(comp_items)
            parts["patterns_count"] = len(pat_items)
            if not parts["tokens"]:
                parts["tokens"] = any(isinstance(data.get(k), dict) for k in TOKEN_SECTION_KEYS)
    except Exception:  # noqa: BLE001
        pass
    return parts


def format_item(row, display_map=None) -> dict:
    """列表/详情条目的 API 返回结构（对齐契约）。

    display_map：account → 显示名（由 resolve_display_map 批量解析后传入，
    列表接口一次解析；单条接口（POST/PATCH/PUT）单独解析）。
    author：恒为对象数组（旧字符串数据自动包装为单元素，见 parse_author_column）。
    """

    def _display(val):
        if not val:
            return val or ""
        return display_map.get(val, val) if display_map else val

    return {
        "slug": row.slug,
        "source_slug": row.source_slug or row.slug,
        "name": row.name,
        "desc": row.desc or "",
        "author": parse_author_column(row.author),
        "usage": row.usage or 0,
        "views": row.views or 0,
        "cover": resolve_cover(row.cover),
        "cover_url": cover_url(row.cover),
        "icon": row.icon or None,
        "icon_url": icon_url(row.icon),
        "json_url": json_url(row.file_path),
        "design_md_url": _to_public_url(row.source_md_path) if row.source_md_path else None,
        "tokens_url": _tokens_url(row),
        "skill_zip_url": _to_public_url(row.skill_zip_path) if row.skill_zip_path else None,
        "skill_name": row.skill_name or None,
        "preview_url": _to_public_url(row.preview_entry_path) if row.preview_entry_path else None,
        "parts": compute_parts(row),
        "default": bool(row.is_default),
        "file_size": row.file_size,
        "created_by": row.created_by or "",
        "updated_by": row.updated_by or "",
        "created_by_name": _display(row.created_by),
        "updated_by_name": _display(row.updated_by),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


# ─────────────────────────── 作者（对象数组） ───────────────────────────

def normalize_authors(raw) -> List[Dict[str, object]]:
    """任意输入 → 作者数组（getAccount 完整值结构，驼峰：{id, userID, account, nickName, dept}）。

    支持：None / 纯字符串（视为 account）/ dict / 对象数组 / 字符串数组；
    兼容旧蛇形字段（nick_name）读取，dept 保留数组原样。
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    if isinstance(raw, str):
        s = raw.strip()
        return [{"account": s, "nickName": ""}] if s else []
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, dict):
            account = str(item.get("account") or "").strip()
            nick = str(item.get("nickName") or item.get("nick_name") or "").strip()
            dept = item.get("dept")
            if isinstance(dept, list):
                dept = [str(d).strip() for d in dept if str(d).strip()]
            elif isinstance(dept, str):
                dept = [dept.strip()] if dept.strip() else []
            else:
                dept = []
            if account or nick:
                out.append({
                    "id": item.get("id"),
                    "userID": str(item.get("userID") or "").strip() or None,
                    "account": account,
                    "nickName": nick,
                    "dept": dept,
                })
        elif isinstance(item, str) and item.strip():
            out.append({"account": item.strip(), "nickName": ""})
    return out


def parse_author_form(val: Optional[str]) -> List[Dict[str, object]]:
    """表单 author 字段 → 数组。优先按 JSON 数组字符串解析，失败按纯字符串处理。"""
    if val is None or str(val).strip() == "":
        return []
    try:
        return normalize_authors(json.loads(val))
    except (ValueError, TypeError):
        return normalize_authors(val)


def parse_author_column(val) -> List[Dict[str, object]]:
    """DB 列值 → 数组（读取时 normalize，不查表；补全在写入时已固化）。

    旧数据兼容：非 JSON 数组的存量字符串按昵称处理（历史上存的是中文名）。
    """
    if not val:
        return []
    if isinstance(val, list):
        return normalize_authors(val)
    s = val.strip() if isinstance(val, str) else str(val)
    if s.startswith("["):
        try:
            return normalize_authors(json.loads(s))
        except (ValueError, TypeError):
            pass
    return [{"account": "", "nickName": s}]


def _dept_display(dept) -> str:
    """users.dept（JSON 数组，最多 4 级）→ 展示字符串（取最末一级；异常回落空）"""
    if isinstance(dept, list):
        for d in reversed(dept):
            if isinstance(d, str) and d.strip():
                return d.strip()
    elif isinstance(dept, str) and dept.strip():
        return dept.strip()
    return ""


def enrich_authors(db, authors: List[Dict[str, object]]) -> None:
    """就地补全：account 非空且缺 nickName 的条目批量查 users 表（dept 一并数组化）。

    正常路径作者来自 /getAccount（自带完整值），此函数兜底手输账号场景；查不到保持原值。
    """
    need = {a["account"] for a in authors if a.get("account") and not a.get("nickName")}
    if not need:
        return
    try:
        from app.models.user import User

        rows = db.query(User.account, User.nick_name, User.dept).filter(User.account.in_(need)).all()
        info = {acc: (nick or "", _dept_display(dept)) for acc, nick, dept in rows}
    except Exception:  # noqa: BLE001
        return
    for a in authors:
        hit = info.get(a.get("account"))
        if hit:
            if not a.get("nickName"):
                a["nickName"] = hit[0]
            if not a.get("dept"):
                a["dept"] = [hit[1]] if hit[1] else []


def resolve_authors(db, form_author: Optional[str], md_author) -> str:
    """组装最终 author 列值（JSON 字符串）：表单优先，回落 MD 派生；normalize + users 表补全。"""
    if form_author is not None and str(form_author).strip():
        authors = parse_author_form(form_author)
    else:
        authors = normalize_authors(md_author)
    enrich_authors(db, authors)
    return json.dumps(authors, ensure_ascii=False)


# ─────────────────────────── 存量迁移（v4.4：json 重建） ───────────────────────────

def migrate_design_systems_json() -> int:
    """存量迁移：全量重建所有未删系统的 design-system.json 为 8+1 键单数据源（v4.4）。

    启动时执行（幂等——从落盘现状重建，结果确定）：老结构（legacy 转换区块 /
    source.files 内嵌源码 / coverage / name·meta 顶层）整体替换为新结构；
    file_size 随 json 重算；file_path 为空的老系统顺带补齐。单系统失败不影响其余。
    """
    from app.database import SessionLocal
    from app.models.design_system import DesignSystem

    n = 0
    session = SessionLocal()
    try:
        rows = session.query(DesignSystem).filter(DesignSystem.is_deleted == 0).all()
        for row in rows:
            try:
                data, _counts = rebuild_design_system_json(row.slug)
                save_json_file(row.slug, data)
                row.file_size = _dir_size(row.slug)
                if not row.file_path:
                    row.file_path = rel_path(row.slug)
                n += 1
            except Exception as e:  # noqa: BLE001
                logger.warning("[migrate] %s design-system.json 重建失败（保留原 json）：%s", row.slug, e)
        session.commit()
    finally:
        session.close()
    if n:
        logger.info("[migrate] design-system.json v4.4 存量重建完成：%d 个系统", n)
    return n


# ─────────────────────────── slug 生成（后端分配，与文件内容解耦） ───────────────────────────

def generate_slug(db) -> str:
    """8 位随机 [a-z0-9]，DB 唯一约束兜底 + 冲突重试。

    slug 只由后端分配（API 路径 / 落盘目录 / 静态 URL），彻底隔离用户输入；
    tokens.json 的 id 原样保留在 source_slug 列（允许重复，仅展示/搜索/追溯）。
    """
    from app.models.design_system import DesignSystem

    for _attempt in range(20):
        slug = "".join(secrets.choice(SLUG_ALPHABET) for _ in range(SLUG_LENGTH))
        if not db.query(DesignSystem).filter(DesignSystem.slug == slug).first():
            return slug
    raise RuntimeError("slug 生成失败：随机空间冲突（理论不可达，请检查数据库）")


# ─────────────────────────── 封面 ───────────────────────────

def cover_rel_path(slug: str, ext: str) -> str:
    """封面相对 FILE_ROOT_DIR 路径（文件名固定用 slug 拼扩展名，无路径注入风险）。"""
    return "%s/%s.%s" % (COVERS_REL_DIR, slug, ext)


def validate_cover_upload(filename: str, content: bytes) -> str:
    """校验封面文件，返回规范扩展名（jpg/png/webp）。失败抛 ValueError。"""
    if len(content) > MAX_COVER_BYTES:
        raise ValueError("封面图片超过 2MB 上限")
    name = (filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext == "jpeg":
        ext = "jpg"
    if ext not in ALLOWED_COVER_EXTS:
        raise ValueError("封面仅支持 jpg/png/webp，收到：%s" % (filename or "未知类型"))
    return ext


def save_cover_file(slug: str, ext: str, content: bytes) -> str:
    """写入封面到 design-systems/covers/{slug}.{ext}，返回相对 FILE_ROOT_DIR 路径。"""
    rel = cover_rel_path(slug, ext)
    path = os.path.join(settings.FILE_ROOT_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return rel


# ─────────────────────────── 图标（支持 svg） ───────────────────────────

BUILTIN_ICONS = ["icon-default.svg"]
DEFAULT_ICON = "icon-default.svg"


def icon_rel_path(slug: str, ext: str) -> str:
    """图标相对 FILE_ROOT_DIR 路径（文件名固定用 slug 拼扩展名，无路径注入风险）。"""
    return "%s/%s.%s" % (ICONS_REL_DIR, slug, ext)


def validate_icon_upload(filename: str, content: bytes) -> str:
    """校验图标文件，返回规范扩展名（jpg/png/webp/svg）。失败抛 ValueError。"""
    if len(content) > MAX_ICON_BYTES:
        raise ValueError("图标文件超过 2MB 上限")
    name = (filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext == "jpeg":
        ext = "jpg"
    if ext not in ALLOWED_ICON_EXTS:
        raise ValueError("图标仅支持 jpg/png/webp/svg，收到：%s" % (filename or "未知类型"))
    return ext


def sanitize_svg(content: bytes) -> bytes:
    """SVG 消毒（防 XSS）：剥离 script 标签 / on* 事件属性 / javascript:、data:text/html URI /
    foreignObject。配合静态服务的 CSP 响应头（main.py）双保险。
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError("SVG 必须是 UTF-8 文本：%s" % e)
    text = re.sub(r"<script[\s\S]*?(?:</script\s*>|$)", "", text, flags=re.I)
    text = re.sub(r"</?script[^>]*>", "", text, flags=re.I)
    text = re.sub(r"\son[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]*)", "", text, flags=re.I)
    text = re.sub(r"<\s*foreignObject[\s\S]*?<\s*/\s*foreignObject\s*>", "", text, flags=re.I)
    text = re.sub(r"<\s*/?\s*foreignObject[^>]*>", "", text, flags=re.I)
    text = re.sub(r"javascript\s*:", "", text, flags=re.I)
    text = re.sub(r"data\s*:\s*text/html", "", text, flags=re.I)
    return text.encode("utf-8")


def save_icon_file(slug: str, ext: str, content: bytes) -> str:
    """写入图标到 design-systems/icons/{slug}.{ext}；svg 先消毒。返回相对路径。"""
    if ext == "svg":
        content = sanitize_svg(content)
    rel = icon_rel_path(slug, ext)
    path = os.path.join(settings.FILE_ROOT_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return rel


def icon_url(icon: Optional[str]) -> str:
    """图标完整 URL：自定义相对路径原样；未设置（None/空）回落内置默认图标 —— 恒有值。

    `icon` 字段本身保持 null=未自定义 的语义，仅 URL 生成时回落默认，便于消费方总能拿到图。
    """
    rel = icon if icon else "%s/%s" % (ICONS_REL_DIR, DEFAULT_ICON)
    return _to_public_url(rel)
