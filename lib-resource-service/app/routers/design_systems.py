"""设计系统管理路由（对齐 requirement/api.md 契约，octo-design-parts/1 五部件格式）

- 列表（api1）/ 五部件上传 / 部件替换（PUT /{slug}/parts）
  / 详情 JSON / 改 meta / 软删
- 上传物为五个可选部件（multipart 各自独立成败，失败部件忽略并回报错误）：
  DESIGN.md（UTF-8 → source.md）/ tokens.json（唯一数据源 → token 区块 + 原件落盘）/
  组件包 zip（components/ 目录，兼容同名多层嵌套）/ Pattern 包 zip（patterns/ 目录，
  同理）/ skill 包 zip（第一层 SKILL.md）；服务端解析为 design-system.json
  （app/services/design_system_zip.py + design_system_service.import_parts）
- slug 由后端生成（8 位随机）；tokens.json 的 id 原样保留在 source_slug（允许重复）
- 存储：FILE_ROOT_DIR/design-systems/{slug}/（design-system.json + source.md +
  tokens.json + skill 包（原文件名） + assets/{components,patterns}/**，经 /static 对外可访问）
- 操作日志复用 operation_log_service；操作人来自 AuthMiddleware 解密的 X-User-Data
"""

import logging
import os
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.design_system import DesignSystem
from app.models.operation_log import OperationLog
from app.services import design_system_service as svc
from app.services import operation_log_service
from app.services.operator import get_operator
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/design-systems", tags=["设计系统"])

# 部件名 → multipart 字段名（请求里的 *_file）
_PART_UPLOAD_FIELDS = {
    "design_md": "design_md_file",
    "tokens": "tokens_file",
    "components": "components_file",
    "patterns": "patterns_file",
    "skill": "skill_file",
}


def _get_by_slug(db: Session, slug: str) -> DesignSystem:
    row = (
        db.query(DesignSystem)
        .filter(DesignSystem.slug == slug, DesignSystem.is_deleted == 0)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="设计系统「%s」不存在" % slug)
    return row


def _log(db, request: Request, action: str, row: DesignSystem, detail=None):
    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=name,
        operator_account=account,
        action=action,
        target_type="design_system",
        target_id=row.id,
        target_name=row.name,
        detail=detail,
    )


def _clear_default(db: Session, except_slug: Optional[str] = None):
    for row in db.query(DesignSystem).filter(DesignSystem.is_default == True, DesignSystem.is_deleted == 0):  # noqa: E712
        if row.slug != except_slug:
            row.is_default = False


async def _read_part_files(**files: Optional[UploadFile]) -> Dict[str, Tuple[str, bytes]]:
    """五个可选部件 UploadFile → {部件名: (文件名, 字节)}（仅含实际提供了的）。

    字段存在但文件名与内容均为空 → 视为未提供（兼容空占位）；
    提供了就交由部件原语校验（含大小/格式），失败走部件级错误回报而非 400。
    """
    parts: Dict[str, Tuple[str, bytes]] = {}
    for part, f in files.items():
        if f is None:
            continue
        content = await f.read()
        if not content and not (f.filename or "").strip():
            continue
        parts[part] = (f.filename or "", content)
    return parts


def _ingest_detail(ingest: dict) -> dict:
    """操作日志 detail 的部件成败摘要（文件大小/计数/技能名/失败原因）。"""
    detail = {}
    for part, info in ingest.items():
        if not info.get("provided"):
            continue
        if info.get("ok"):
            summary = {k: v for k, v in info.items() if k not in ("provided", "ok")}
            detail[part] = summary or "ok"
        else:
            detail[part] = "失败：%s" % info.get("error")
    return detail


# ─────────────────────────── 1. 列表（api1） ───────────────────────────

@router.get("")
def list_design_systems(
    search: Optional[str] = Query(None, description="按名称/slug/规范id(source_slug)/作者模糊搜索"),
    db: Session = Depends(get_db),
):
    q = db.query(DesignSystem).filter(DesignSystem.is_deleted == 0)
    if search and search.strip():
        kw = "%%%s%%" % search.strip()
        q = q.filter(
            or_(
                DesignSystem.name.ilike(kw),
                DesignSystem.slug.ilike(kw),
                DesignSystem.source_slug.ilike(kw),
                DesignSystem.author.ilike(kw),
            )
        )
    # slug 为后端随机分配（字典序无意义），非默认系统按创建时间倒序（新上传靠前）
    rows = q.order_by(DesignSystem.is_default.desc(), DesignSystem.created_at.desc()).all()
    display_map = svc.resolve_display_map(
        db, [a for r in rows for a in (r.created_by, r.updated_by)]
    )
    items = [svc.format_item(r, display_map) for r in rows]
    return {"count": len(items), "items": items}


# ─────────────────────────── 操作记录 ───────────────────────────

@router.get("/operation-logs")
def list_operation_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None, description="create/update_meta/update_parts/delete/update"),
    target_type: Optional[str] = Query(None, description="design_system/ds_whitelist"),
    db: Session = Depends(get_db),
):
    """设计系统模块操作记录：固定 target_type IN (design_system, ds_whitelist)，id 倒序分页。"""
    q = db.query(OperationLog).filter(
        OperationLog.target_type.in_(("design_system", "ds_whitelist"))
    )
    if action:
        q = q.filter(OperationLog.action == action)
    if target_type:
        q = q.filter(OperationLog.target_type == target_type)
    total = q.count()
    items = (
        q.order_by(OperationLog.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "items": [operation_log_service.format_log(i) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


# ─────────────────────────── 2. 上传（五部件，全部可选、独立成败） ───────────────────────────

@router.post("")
async def create_design_system(
    request: Request,
    db: Session = Depends(get_db),
    name: Optional[str] = Form(None, description="卡片名称（必填；部件全空也允许——纯壳系统）"),
    desc: Optional[str] = Form(None),
    author: Optional[str] = Form(None, description="作者，JSON 数组字符串 [{account, nick_name, dept}]；缺省回落 tokens.json meta 派生"),
    usage: Optional[str] = Form(None),
    cover: Optional[str] = Form(None),
    default: Optional[str] = Form(None),
    design_md_file: Optional[UploadFile] = File(None, description="部件①：DESIGN.md（UTF-8 文本，原文存 source.md）"),
    tokens_file: Optional[UploadFile] = File(None, description="部件②：tokens.json（唯一数据源：UTF-8 合法 JSON）"),
    components_file: Optional[UploadFile] = File(None, description="部件③：组件包 zip（根须含 components/ 目录；兼容 components/components/ 同名嵌套）"),
    patterns_file: Optional[UploadFile] = File(None, description="部件④：Pattern 包 zip（根须含 patterns/ 目录；兼容同名嵌套）"),
    skill_file: Optional[UploadFile] = File(None, description="部件⑤：skill 包 zip（第一层须含 SKILL.md，frontmatter name 非空）"),
    cover_file: Optional[UploadFile] = File(None, description="可选封面图片（jpg/png/webp ≤2MB）"),
    icon_file: Optional[UploadFile] = File(None, description="可选图标（jpg/png/webp/svg ≤2MB）"),
):
    """五部件上传新增：逐部件独立成败——失败部件忽略并在响应 ingest 里回报错误，其余部件正常入库。"""
    name_val = (name or "").strip()
    part_files = await _read_part_files(
        design_md=design_md_file, tokens=tokens_file,
        components=components_file, patterns=patterns_file, skill=skill_file,
    )
    # 名称必填：表单 name 或 tokens.json 的 name 至少提供其一（后者 tokens 解析后由
    # import_parts 写入 json.name；此处仅能预判「两者都不可能提供」的场景）
    if not name_val and "tokens" not in part_files:
        raise HTTPException(status_code=400, detail="名称不能为空（表单 name 或 tokens.json 的 name 至少提供其一）")
    result = svc.import_parts(db, part_files, existing=None, name_override=name_val or None)
    final_name = name_val or str(result["data"].get("name") or "").strip()
    if not final_name:
        raise HTTPException(status_code=400, detail="名称不能为空")

    meta = svc.extract_meta(result["data"])
    # 表单覆盖派生值（name 已在 import_parts 写入 json = 表单值）
    if desc is not None and desc != "":
        meta["desc"] = desc
    if cover:
        meta["cover"] = svc.normalize_cover(cover)
    usage_val = None
    if usage is not None and str(usage).strip() != "":
        try:
            usage_val = svc.parse_form_int(usage)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if usage_val is None:
        # 需求明确：md 里的 usage 不允许直接使用 —— 新增系统恒 0 起步
        usage_val = 0
    # 作者：表单（JSON 数组字符串）优先，回落 tokens.json meta 派生；写入时经 users 表补全昵称/部门
    author_json = svc.resolve_authors(db, author, meta.get("author"))
    # 自定义封面图片：上传则覆盖内置名（文件名固定 {slug}.{ext}）
    if cover_file is not None:
        cover_content = await cover_file.read()
        try:
            ext = svc.validate_cover_upload(cover_file.filename, cover_content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        meta["cover"] = svc.save_cover_file(result["slug"], ext, cover_content)
    # 自定义图标
    icon_rel = None
    if icon_file is not None:
        icon_content = await icon_file.read()
        try:
            ext = svc.validate_icon_upload(icon_file.filename, icon_content)
            icon_rel = svc.save_icon_file(result["slug"], ext, icon_content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    default_val = svc.parse_form_bool(default)
    account, _op_name = get_operator(request)
    row = DesignSystem(
        slug=result["slug"],
        source_slug=result["source_slug"],
        name=final_name,
        desc=meta["desc"] or None,
        author=author_json,
        icon=icon_rel,
        usage=usage_val,
        cover=meta["cover"],
        is_default=bool(default_val) if default_val is not None else False,
        file_path=svc.rel_path(result["slug"]),
        source_md_path=result["source_md_rel"],
        skill_zip_path=result["skill_zip_rel"],
        skill_name=result["skill_name"],
        file_size=result["file_size"],
        created_by=account,
        updated_by=account,
        is_deleted=0,
    )
    if row.is_default:
        _clear_default(db, row.slug)
    db.add(row)
    db.commit()
    db.refresh(row)
    _log(db, request, "create", row, {
        "slug": row.slug, "source_slug": row.source_slug,
        "parts": _ingest_detail(result["ingest"]),
    })
    return {
        **svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by])),
        "ingest": result["ingest"],
    }


# ─────────────────────────── 5. 部件替换（PUT /{slug}/parts） ───────────────────────────

@router.put("/{slug}/parts")
async def put_design_system_parts(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    design_md_file: Optional[UploadFile] = File(None, description="替换部件①：DESIGN.md（UTF-8 文本）"),
    tokens_file: Optional[UploadFile] = File(None, description="替换部件②：tokens.json（唯一数据源）"),
    components_file: Optional[UploadFile] = File(None, description="替换部件③：组件包 zip（只换 assets/components 子树）"),
    patterns_file: Optional[UploadFile] = File(None, description="替换部件④：Pattern 包 zip（只换 assets/patterns 子树）"),
    skill_file: Optional[UploadFile] = File(None, description="替换部件⑤：skill 包 zip（原文件名落盘，旧附件自动清理）"),
):
    """部件替换：仅替换提供部件的内容（逐部件独立成败）；未提供部件取存量。

    - tokens 未提供 → 存量 json 的 token 区块原样保留（老系统无 tokens 原件同样兼容）
    - meta（名称/作者/封面/图标/调用量/描述/默认标记）不受影响，走 PATCH /{slug}
    """
    row = _get_by_slug(db, slug)
    part_files = await _read_part_files(
        design_md=design_md_file, tokens=tokens_file,
        components=components_file, patterns=patterns_file, skill=skill_file,
    )
    if not part_files:
        raise HTTPException(status_code=400, detail="未提供任何部件文件")
    result = svc.import_parts(db, part_files, existing=row)

    # DB 列更新：仅部件成功提供时（未提供的部件保留存量指针）
    if result["source_md_rel"]:
        row.source_md_path = result["source_md_rel"]
    if result["skill_zip_rel"]:
        row.skill_zip_path = result["skill_zip_rel"]
        row.skill_name = result["skill_name"]
    row.file_size = result["file_size"]
    account, _ = get_operator(request)
    row.updated_by = account
    db.commit()
    db.refresh(row)
    _log(db, request, "update_parts", row, {
        "slug": slug,
        "parts": _ingest_detail(result["ingest"]),
    })
    return {
        **svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by])),
        "ingest": result["ingest"],
    }


# ─────────────────────────── 3. 详情 JSON ───────────────────────────

@router.get("/{slug}/json")
def get_design_system_json(slug: str, db: Session = Depends(get_db)):
    row = _get_by_slug(db, slug)
    path = os.path.join(settings.FILE_ROOT_DIR, row.file_path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="JSON 文件缺失：%s" % row.file_path)
    return FileResponse(path, media_type="application/json", filename="design-system.json")


# ─────────────────────────── 4. 编辑卡片 meta ───────────────────────────

@router.patch("/{slug}")
async def patch_design_system(
    slug: str,
    request: Request,
    name: Optional[str] = Form(None),
    desc: Optional[str] = Form(None),
    author: Optional[str] = Form(None, description="作者，JSON 数组字符串 [{account, nick_name, dept}]；空数组清空作者"),
    usage: Optional[str] = Form(None),
    views: Optional[str] = Form(None, description="预览量修正通道（仅 API 层，界面无编辑入口）；非负整数、整字段覆盖"),
    default: Optional[str] = Form(None),
    cover_file: Optional[UploadFile] = File(None, description="可选新封面（jpg/png/webp ≤2MB）；不上传则保留现有封面"),
    icon_file: Optional[UploadFile] = File(None, description="可选新图标（jpg/png/webp/svg ≤2MB）；不上传则保留现有图标"),
    db: Session = Depends(get_db),
):
    row = _get_by_slug(db, slug)
    detail = {}
    if name is not None:
        if not name.strip():
            raise HTTPException(status_code=400, detail="名称不能为空")
        row.name = name.strip()
        detail["name"] = row.name
    if desc is not None:
        row.desc = desc
        detail["desc"] = desc
    if author is not None:
        row.author = svc.resolve_authors(db, author, None)
        detail["author"] = svc.parse_author_column(row.author)
    if usage is not None and usage.strip() != "":
        try:
            row.usage = svc.parse_form_int(usage)
            detail["usage"] = row.usage
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if views is not None and views.strip() != "":
        try:
            row.views = svc.parse_form_int(views, "预览量")
            if row.views < 0:
                raise ValueError("预览量必须为非负整数")
            detail["views"] = row.views
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if cover_file is not None:
        content = await cover_file.read()
        try:
            ext = svc.validate_cover_upload(cover_file.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        rel = svc.save_cover_file(slug, ext, content)
        row.cover = rel
        detail["cover"] = rel
    if icon_file is not None:
        content = await icon_file.read()
        try:
            ext = svc.validate_icon_upload(icon_file.filename, content)
            rel = svc.save_icon_file(slug, ext, content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        row.icon = rel
        detail["icon"] = rel
    account, _ = get_operator(request)
    row.updated_by = account
    if default is not None:
        dv = svc.parse_form_bool(default)
        if dv is True:
            _clear_default(db, slug)
            row.is_default = True
            detail["default"] = True
        elif dv is False:
            row.is_default = False
            detail["default"] = False
    db.commit()
    db.refresh(row)
    _log(db, request, "update_meta", row, detail or None)
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))


# ─────────────────────────── 7. 调用量自增 ───────────────────────────

def _increment_with_event(slug: str, request: Request, db: Session, column: str, event_type: str, op_override=None):
    """usage / views 自增 + 打点事件写入（同一事务，保证统计口径与累计列一致）。

    - 身份来自 X-User-Data（AuthMiddleware 解密），写入前经 resolve_user_info 三级兜底完整化；
      op_override 非空时（POST /usage/report 的 account 上报场景）以其替代 request 解密身份
    - 高频调用，不写操作日志、不改动 updated_at（那是内容/管理字段的更新时间）
    - SQL 端自增（避免并发读改写丢失）；事件插入与自增同 commit，失败整体回滚
    """
    from app.models.ds_usage_event import DsUsageEvent
    from app.services.operator import get_operator
    from app.services.user_info_service import resolve_user_info, snapshot_fields

    row = (
        db.query(DesignSystem)
        .filter(DesignSystem.slug == slug, DesignSystem.is_deleted == 0)
        .first()
    )
    if not row:
        logger.info("[ds-track] 打点丢弃：slug=%s 不存在/已软删（event=%s）", slug, event_type)
        raise HTTPException(status_code=404, detail="设计系统「%s」不存在" % slug)

    # 身份完整化（可能含 getAccount 外部查询）放在事务性写入之前，失败降级不丢打点
    info = resolve_user_info(db, op_override if op_override is not None else get_operator(request))
    account, nick_name, dept1, dept2, dept3, dept4 = snapshot_fields(info)
    logger.info("[ds-track] event=%s slug=%s account=%s", event_type, slug, account or "（匿名）")

    # 匿名（account 为空，仅 7a 豁免可发生；7 须登录态、7b 缺 account 直接 400）不写打点事件：
    # 事件表不再产生空 account 行；views/usage 累计列照常自增（曝光量语义），
    # 统计侧由 _range_query 统一排除存量匿名行，两端口径一致
    if account:
        db.add(DsUsageEvent(
            slug=slug, event_type=event_type,
            account=account, nick_name=nick_name or None,
            dept1=dept1, dept2=dept2, dept3=dept3, dept4=dept4,
        ))
    db.query(DesignSystem).filter(
        DesignSystem.slug == slug, DesignSystem.is_deleted == 0
    ).update(
        {
            column: getattr(DesignSystem, column) + 1,
            # 显式提供 updated_at 覆盖列级 onupdate，保持其语义不变
            "updated_at": DesignSystem.updated_at,
        },
        synchronize_session=False,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("[ds-track] ✗ 提交失败：slug=%s event=%s", slug, event_type, exc_info=True)
        raise
    db.refresh(row)
    logger.info("[ds-track] ✓ slug=%s %s=%s 事件行%s", slug, column, getattr(row, column),
                "已写入" if account else "跳过（匿名）")
    return row


@router.post("/{slug}/usage")
def increment_usage(slug: str, request: Request, db: Session = Depends(get_db)):
    """使用方（如 Octo Design）显式调用，usage += 1，同时写入打点事件（建议携带 X-User-Data）。"""
    row = _increment_with_event(slug, request, db, "usage", "usage")
    return {"slug": slug, "usage": row.usage}


# ─────────────────────────── 7b. 调用量上报（免登录态，传 account） ───────────────────────────

class UsageReportBody(BaseModel):
    slug: str = Field(..., min_length=1, description="设计系统 slug")
    account: str = Field("", description="用户账号（无有效 X-User-Data 时必填；后端查询补全 nickName/dept）")


@router.post("/usage/report")
def usage_report(body: UsageReportBody, request: Request, db: Session = Depends(get_db)):
    """免登录态的调用量上报：slug + account 放消息体，用户信息由后端查询补全后入库。

    - 逻辑与 POST /{slug}/usage（7 号）完全一致：usage+1 + 同事务打点事件
    - 完全公开：免登录、免权限校验（在登录过期豁免清单内，路径精确匹配）
    - 身份优先级：有效 X-User-Data > body.account；两者皆无 → 400
    - account 经 resolve_user_info 三级兜底（users 表 → getAccount 人员服务 → 回写缓存）
      补全昵称/部门后写事件快照；查无此人降级照写（nick_name/dept 留空，绝不丢打点）
    """
    from app.services.operator import OperatorInfo

    op = get_operator(request)
    has_valid_op = bool(op) and op.account not in ("", "unknown")
    account = (body.account or "").strip()
    if not has_valid_op and not account:
        raise HTTPException(status_code=400, detail="缺少 account（且未携带有效 X-User-Data）")
    if not has_valid_op:
        op = OperatorInfo(account=account)
    row = _increment_with_event(body.slug.strip(), request, db, "usage", "usage", op_override=op)
    return {"slug": row.slug, "usage": row.usage}


# ─────────────────────────── 7c. 打点事件用户信息补全（公开维护接口） ───────────────────────────

class RefreshIdentityBody(BaseModel):
    accounts: list = Field([], description="限定补全的账号列表；空 = 全表扫描身份不完整的事件")


@router.post("/events/refresh-identity")
def events_refresh_identity(body: RefreshIdentityBody, db: Session = Depends(get_db)):
    """打点事件用户信息补全：只补空、不修订已有快照（完全公开，幂等）。

    - 候选：account 非空且 nick_name 或 dept1 为空的事件（body.accounts 可限定范围）
    - 逐账号走 resolve 链（users 表 → getAccount 人员服务 → 回写缓存）后逐字段补空；
      事件内已有值的字段一律不动；查不到的账号进 unresolved，事件原样保留
    - 匿名事件（account 为空）永不触碰；响应 {"accounts_total", "resolved", "unresolved", "events_updated"}
    """
    from app.services import ds_stats_service as stats
    return stats.refresh_event_identities(db, accounts=body.accounts)


# ─────────────────────────── 7d. 预览量纠正（公开维护） ───────────────────────────

class CorrectViewsBody(BaseModel):
    slug: str = Field(..., min_length=1, description="设计系统 slug")
    views: int = Field(..., ge=0, description="纠正后的预览量（非负整数，绝对值覆盖）")


@router.post("/views/correct")
def correct_views(body: CorrectViewsBody, request: Request, db: Session = Depends(get_db)):
    """预览量纠正（公开维护接口，免登录态）：手动修正历史错误数据的运维通道。

    - 与 PATCH 的 `views` 修正字段同语义：非负整数、**整字段覆盖**（绝对值，非增量）
    - **完全公开**（在登录过期豁免清单内）——只开放「纠正预览量」这一个动作；PATCH 等
      管理写操作仍需登录态。无 X-User-Data 时操作日志记 unknown、updated_by 不动；
      携带则记实际操作人
    - 软删/不存在的 slug → 404
    """
    row = (
        db.query(DesignSystem)
        .filter(DesignSystem.slug == body.slug.strip(), DesignSystem.is_deleted == 0)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="设计系统「%s」不存在" % body.slug)
    row.views = body.views
    account, _ = get_operator(request)
    if account and account != "unknown":
        row.updated_by = account
    db.commit()
    db.refresh(row)
    _log(db, request, "update_meta", row, {"views": row.views, "channel": "views/correct"})
    return {"slug": row.slug, "views": row.views}


# ─────────────────────────── 7a. 预览量自增 ───────────────────────────

@router.post("/{slug}/views")
def increment_views(slug: str, request: Request, db: Session = Depends(get_db)):
    """展示端设计系统详情页每次加载时调用，views += 1，同时写入打点事件
    （展示端携带 X-User-Data，事件快照 account/nickName/dept 供统计页聚合）。"""
    row = _increment_with_event(slug, request, db, "views", "view")
    return {"slug": slug, "views": row.views}


# ─────────────────────────── 10. 打点统计（管理台数据统计页） ───────────────────────────

@router.get("/stats/summary")
def stats_summary(
    start: str = Query("", description="起始日期 YYYY-MM-DD（缺省不限）"),
    end: str = Query("", description="结束日期 YYYY-MM-DD（缺省不限）"),
    search: str = Query("", description="按设计系统名称模糊搜索"),
    db: Session = Depends(get_db),
):
    """左表：每系统 预览数/调用量/使用人数/最近调用时间 + 全局汇总行（无数据系统补 0）。"""
    from app.services import ds_stats_service as stats
    return stats.stats_summary(db, start, end, search)


@router.get("/stats/trend")
def stats_trend(
    metric: str = Query("view", description="view 预览数 / usage 调用量 / users 引用人数"),
    granularity: str = Query("day", description="day / week / month"),
    start: str = Query(""),
    end: str = Query(""),
    db: Session = Depends(get_db),
):
    """条形图：时间桶 × 一层部门（dept1）→ 指标值（前端透视为堆叠柱状图）。"""
    from app.services import ds_stats_service as stats
    if metric not in stats.METRICS:
        raise HTTPException(status_code=400, detail="metric 仅支持 %s" % "/".join(stats.METRICS))
    if granularity not in stats.GRANULARITIES:
        raise HTTPException(status_code=400, detail="granularity 仅支持 %s" % "/".join(stats.GRANULARITIES))
    return stats.stats_trend(db, metric, granularity, start, end)


@router.get("/stats/dept-share")
def stats_dept_share(
    metric: str = Query("view"),
    start: str = Query(""),
    end: str = Query(""),
    db: Session = Depends(get_db),
):
    """扇形图：一层部门（dept1）指标占比。"""
    from app.services import ds_stats_service as stats
    if metric not in stats.METRICS:
        raise HTTPException(status_code=400, detail="metric 仅支持 %s" % "/".join(stats.METRICS))
    return stats.stats_dept_share(db, metric, start, end)


@router.get("/stats/users")
def stats_users(
    start: str = Query(""),
    end: str = Query(""),
    search: str = Query("", description="按工号/名字模糊搜索"),
    db: Session = Depends(get_db),
):
    """人员统计表：工号/名字/最近调用时间/预览数/调用量/一~四层部门（快照）。"""
    from app.services import ds_stats_service as stats
    return stats.stats_users(db, start, end, search)


# ─────────────────────────── 6. 删除（软删） ───────────────────────────

@router.delete("/{slug}")
def delete_design_system(slug: str, request: Request, db: Session = Depends(get_db)):
    row = _get_by_slug(db, slug)
    row.is_deleted = 1
    account, _ = get_operator(request)
    row.updated_by = account
    db.commit()
    _log(db, request, "delete", row, {"slug": slug})
    return {"detail": "ok"}


# ─────────────────────────── 1a. 单条详情（api1 item 同构） ───────────────────────────

@router.get("/{slug}")
def get_design_system(slug: str, db: Session = Depends(get_db)):
    """单条详情：与列表 item 完全同构（format_item 同一产物——name/usage/views/author/
    parts/各下载 URL/file_size 等全字段），展示端详情页数据源。

    - 建议消费顺序：进页先 POST /{slug}/views 打点、再 GET 本接口——返回的 views
      已含本次浏览，头部一次渲染无「快照→自增」跳变
    - 匿名可访问（登录过期豁免清单内，与列表接口同等待遇——展示端匿名浏览详情依赖）
    - slug 不存在/软删 → 404

    路由注册位置：本路由为单段路径参数，必须注册在 GET /operation-logs（本文件内）
    之后；main.py 中 ds_whitelist.router（GET /api/design-systems/whitelist 单段）
    必须 include 在本 router 之前，否则会被 /{slug} 劫持。
    """
    row = _get_by_slug(db, slug)
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))
