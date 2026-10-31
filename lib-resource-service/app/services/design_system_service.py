"""设计系统业务逻辑：JSON 校验、卡片 meta 派生、文件存储。

校验与语义严格对齐 requirement/api.md 契约（前端 mock：design-system-admin/src/api/mock.ts）：
- slug = JSON 的 id，格式 ^[a-z0-9][a-z0-9-]*$，唯一
- name 非空；color/typography/spacing/radius/shadow 至少一个区块
- cover 不在内置封面集时回落默认（不报错）
- 重传覆盖：name/cover 跟随新 JSON，作者/调用量/描述/默认标记保留
"""

import json
import os
import re
from typing import Optional, Tuple

from app.config import settings

BUILTIN_COVERS = ["cover-blue.jpg", "cover-cyan.jpg", "cover-purple.jpg", "cover-violet.jpg"]
DEFAULT_COVER = "cover-cyan.jpg"
MAX_JSON_BYTES = 10 * 1024 * 1024
MAX_COVER_BYTES = 2 * 1024 * 1024
ALLOWED_COVER_EXTS = {"jpg", "jpeg", "png", "webp"}
COVERS_REL_DIR = "design-systems/covers"
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
    """

    def _display(val):
        if not val:
            return val or ""
        return display_map.get(val, val) if display_map else val

    return {
        "slug": row.slug,
        "name": row.name,
        "desc": row.desc or "",
        "author": row.author or "",
        "usage": row.usage or 0,
        "cover": resolve_cover(row.cover),
        "cover_url": cover_url(row.cover),
        "json_url": json_url(row.file_path),
        "default": bool(row.is_default),
        "file_size": row.file_size,
        "created_by": row.created_by or "",
        "updated_by": row.updated_by or "",
        "created_by_name": _display(row.created_by),
        "updated_by_name": _display(row.updated_by),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def parse_upload(content: bytes) -> Tuple[dict, list]:
    """字节 → (data, errors)。JSON 解析与结构校验一并完成。"""
    try:
        data = json.loads(content.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return None, ["JSON 解析失败：%s" % e]
    return data, validate_design_system_json(data)


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
