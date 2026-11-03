"""设计系统业务逻辑：DESIGN.md 解析与校验、卡片 meta 派生、作者/封面/图标、文件存储。

校验与语义严格对齐 requirement/api.md 契约：
- 上传只收 DESIGN.md（octo-design-md/1 格式），服务端解析为 design-system.json
- slug = 解析结果的 id，格式 ^[a-z0-9][a-z0-9-]*$，唯一
- name 非空；color/typography/spacing/radius/shadow 至少一个区块
- author 为对象数组 [{account, nick_name, dept}]，写入时经 users 表补全昵称/部门（固化存储）；
  旧字符串数据读取时自动包装为单元素数组（无需迁移）
- cover 不在内置封面集时回落默认（不报错）；icon 支持自定义上传（jpg/png/webp/svg）
- 重传覆盖：name 跟随新 MD，作者/封面/图标/调用量/描述/默认标记保留
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services import design_system_md

BUILTIN_COVERS = ["cover-blue.jpg", "cover-cyan.jpg", "cover-purple.jpg", "cover-violet.jpg"]
DEFAULT_COVER = "cover-cyan.jpg"
MAX_JSON_BYTES = 10 * 1024 * 1024
MAX_COVER_BYTES = 2 * 1024 * 1024
ALLOWED_COVER_EXTS = {"jpg", "jpeg", "png", "webp"}
COVERS_REL_DIR = "design-systems/covers"
MAX_ICON_BYTES = 2 * 1024 * 1024
ALLOWED_ICON_EXTS = {"jpg", "jpeg", "png", "webp", "svg"}
ICONS_REL_DIR = "design-systems/icons"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_SECTIONS = ["color", "typography", "spacing", "radius", "shadow"]


def validate_design_system_json(data) -> list:
    """校验 design-system.json 结构，返回错误列表（空 = 通过）"""
    if not isinstance(data, dict):
        return ["文件内容不是 JSON 对象"]

    errors = []
    slug = data.get("id")
    if not isinstance(slug, str) or not slug:
        errors.append("缺少 id 字段（作为系统唯一标识 slug）")
    elif not SLUG_RE.match(slug):
        errors.append("id「%s」格式非法：仅允许小写字母、数字、连字符，且以字母或数字开头" % slug)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("缺少 name 字段或为空")

    has_section = any(isinstance(data.get(k), dict) and data.get(k) is not None for k in REQUIRED_SECTIONS)
    if not has_section:
        errors.append("缺少可展示的 token 区块（%s 至少一项）" % " / ".join(REQUIRED_SECTIONS))

    return errors


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
    """从 JSON 派生卡片 meta（管理字段默认值，可被表单覆盖）"""
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    usage = meta.get("usage")
    return {
        "slug": str(data.get("id") or ""),
        "name": str(data.get("name") or ""),
        "desc": meta.get("desc") if isinstance(meta.get("desc"), str) else "",
        "author": meta.get("author") if isinstance(meta.get("author"), str) else "",
        "usage": usage if isinstance(usage, int) else 0,
        "cover": normalize_cover(data.get("cover")),
        "default": False,
    }


def rel_path(slug: str) -> str:
    """JSON 文件相对 FILE_ROOT_DIR 的路径"""
    return "design-systems/%s/design-system.json" % slug


def abs_path(slug: str) -> str:
    return os.path.join(settings.FILE_ROOT_DIR, rel_path(slug))


def save_json_file(slug: str, data: dict, file_size: int) -> None:
    """写入 JSON 文件到 FILE_ROOT_DIR/design-systems/{slug}/design-system.json"""
    path = abs_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    _ = file_size  # 尺寸由调用方记录到 DB


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


def parse_form_int(val) -> Optional[int]:
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(str(val).strip())
    except ValueError:
        raise ValueError("调用量必须为整数，收到：%s" % val)


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
        "name": row.name,
        "desc": row.desc or "",
        "author": parse_author_column(row.author),
        "usage": row.usage or 0,
        "cover": resolve_cover(row.cover),
        "cover_url": cover_url(row.cover),
        "icon": row.icon or None,
        "icon_url": icon_url(row.icon),
        "json_url": json_url(row.file_path),
        "design_md_url": _to_public_url(row.source_md_path) if row.source_md_path else None,
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


# ─────────────────────────── MD 上传与存储 ───────────────────────────

def parse_md_upload(content: bytes) -> dict:
    """DESIGN.md 字节 → design-system.json 同构 dict（解析失败抛 ValueError）。"""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError("DESIGN.md 必须是 UTF-8 文本：%s" % e)
    return design_system_md.parse_md(text)


def source_md_rel_path(slug: str) -> str:
    """DESIGN.md 原件相对 FILE_ROOT_DIR 的路径（固定命名）"""
    return "design-systems/%s/source.md" % slug


def save_source_md(slug: str, content: bytes) -> str:
    """保存 MD 原件到 design-systems/{slug}/source.md，返回相对路径（存 DB source_md_path 列）。"""
    path = os.path.join(settings.FILE_ROOT_DIR, source_md_rel_path(slug))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return source_md_rel_path(slug)


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
