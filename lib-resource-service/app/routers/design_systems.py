"""设计系统管理路由（对齐 requirement/api.md 契约）

- 列表（api1）/ zip 上传 / 解析预览（parse）/ 分片上传（init/chunk/complete）
  / 详情 JSON / 改 meta / zip 重传覆盖 / 软删
- 上传物为 zip 包（DESIGN.md + assets + 任意名 .zip 附件，octo-design-zip/1），
  服务端解压解析为 design-system.json（app/services/design_system_zip.py）
- slug 由后端生成（8 位随机）；MD 的 id 原样保留在 source_slug（允许重复）
- 存储：FILE_ROOT_DIR/design-systems/{slug}/（design-system.json + source.zip +
  source.md + 附件（原文件名） + assets/**，经 /static 对外可访问）
- 操作日志复用 operation_log_service；操作人来自 AuthMiddleware 解密的 X-User-Data
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.design_system import DesignSystem
from app.models.operation_log import OperationLog
from app.services import design_system_service as svc
from app.services import design_system_zip as dzip
from app.services import operation_log_service
from app.services.operator import get_operator
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/design-systems", tags=["设计系统"])


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


def _check_zip_ext(filename: Optional[str]):
    """上传只收 zip 包（octo-design-zip/1：DESIGN.md + assets + 任意名 .zip 附件）"""
    ext = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else ""
    if ext != "zip":
        raise HTTPException(status_code=400, detail="仅支持上传 zip 包（octo-design-zip/1 格式：DESIGN.md + assets + 附件 .zip），收到：%s" % (filename or "未知文件"))


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
    action: Optional[str] = Query(None, description="create/update_meta/reupload/delete/update"),
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


# ─────────────────────────── zip 解析预览（不落库） ───────────────────────────

@router.post("/parse")
async def parse_design_system_zip(
    file: UploadFile = File(..., description="zip 包（octo-design-zip/1）；解析返回 design-system.json + 统计，不落库"),
):
    """管理台「Zip 解析」预览页数据源：上传 zip → md 转 json + assets 树扫描结果。

    校验同正式上传（zip 安全 + MD 解析 + design-system.json 结构）：
    预览阶段即拦截不可入库的包（缺 token 区块等），对齐 api.md 契约。
    """
    _check_zip_ext(file.filename)
    content = await file.read()
    try:
        result = dzip.parse_zip_info(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    errors = svc.validate_design_system_json(result["ds"])
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))
    return result


# ─────────────────────────── 分片上传（大 zip：>20MB 由前端自动切换） ───────────────────────────

class UploadInitBody(BaseModel):
    filename: str
    size: int


@router.post("/uploads/init")
def upload_init(body: UploadInitBody):
    """创建分片上传会话：{upload_id, chunk_size(5MB), chunk_count}。

    会话目录 FILE_ROOT_DIR/design-systems/uploads/{upload_id}/，TTL 24h 自动清理。
    """
    try:
        return dzip.upload_init(body.filename, body.size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/uploads/{upload_id}/chunks/{index}")
async def upload_chunk(upload_id: str, index: int, request: Request):
    """写入第 index 片（raw binary body，Content-Type: application/octet-stream）。"""
    body = await request.body()
    try:
        return dzip.upload_chunk(upload_id, index, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/uploads/{upload_id}/complete")
async def upload_complete(
    upload_id: str,
    request: Request,
    name: Optional[str] = Form(None),
    desc: Optional[str] = Form(None),
    author: Optional[str] = Form(None, description="作者，JSON 数组字符串 [{account, nick_name, dept}]；缺省回落 MD 派生"),
    usage: Optional[str] = Form(None),
    default: Optional[str] = Form(None),
    slug: Optional[str] = Form(None, description="重传模式：目标系统 slug（对齐 PUT /{slug}/json 语义）；缺省为新增"),
    cover_file: Optional[UploadFile] = File(None, description="可选封面图片（jpg/png/webp ≤2MB）"),
    icon_file: Optional[UploadFile] = File(None, description="可选图标（jpg/png/webp/svg ≤2MB）"),
    db: Session = Depends(get_db),
):
    """合并分片 → zip 导入。slug 表单字段提供时走重传（内容替换、管理字段保留），否则新增。"""
    try:
        content, filename = dzip.upload_merge(upload_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        if slug:
            row = _reupload_zip(db, request, slug, content, filename)
        else:
            row = await _create_from_zip(
                db, request, content, filename,
                name=name, desc=desc, author=author, usage=usage,
                default=default, cover_file=cover_file, icon_file=icon_file,
            )
            db.commit()
            db.refresh(row)
            _log(db, request, "create", row, {
                "slug": row.slug, "source_slug": row.source_slug,
                "file": filename, "size": len(content), "chunked": True,
            })
        db.commit()
        db.refresh(row)
        dzip.upload_discard(upload_id)
        return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))
    except HTTPException:
        # 导入失败（zip 内容/结构问题居多）：会话无重试价值，直接清理避免占磁盘
        dzip.upload_discard(upload_id)
        raise


# ─────────────────────────── 2. 上传（zip 直传） ───────────────────────────

@router.post("")
async def create_design_system(
    request: Request,
    file: UploadFile = File(..., description="zip 包（octo-design-zip/1 格式，≤200MB；服务端解压解析为 design-system.json）"),
    name: Optional[str] = Form(None),
    desc: Optional[str] = Form(None),
    author: Optional[str] = Form(None, description="作者，JSON 数组字符串 [{account, nick_name, dept}]；缺省回落 MD 派生"),
    usage: Optional[str] = Form(None),
    cover: Optional[str] = Form(None),
    default: Optional[str] = Form(None),
    cover_file: Optional[UploadFile] = File(None, description="可选封面图片（jpg/png/webp ≤2MB）"),
    icon_file: Optional[UploadFile] = File(None, description="可选图标（jpg/png/webp/svg ≤2MB）"),
    db: Session = Depends(get_db),
):
    _check_zip_ext(file.filename)
    content = await file.read()
    if len(content) > dzip.MAX_ZIP_BYTES:
        raise HTTPException(status_code=413, detail="zip 包超过 %dMB 上限" % (dzip.MAX_ZIP_BYTES // 1024 // 1024))
    row = await _create_from_zip(
        db, request, content, file.filename,
        name=name, desc=desc, author=author, usage=usage,
        cover=cover, default=default, cover_file=cover_file, icon_file=icon_file,
    )
    db.commit()
    db.refresh(row)
    _log(db, request, "create", row, {"slug": row.slug, "source_slug": row.source_slug, "file": file.filename, "size": len(content)})
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))


async def _create_from_zip(
    db: Session,
    request: Request,
    content: bytes,
    filename: Optional[str],
    *,
    name: Optional[str],
    desc: Optional[str],
    author: Optional[str],
    usage: Optional[str],
    cover: Optional[str] = None,
    default: Optional[str] = None,
    cover_file: Optional[UploadFile],
    icon_file: Optional[UploadFile],
) -> DesignSystem:
    """zip 导入 + 新建记录（直传 POST 与分片 complete 共用；调用方负责 commit/日志）。

    - slug 后端随机生成（无冲突/无 409/无软删复活），source_slug 原样保留 MD id（允许重复）
    - usage 恒 0 起步（MD frontmatter 的 usage 不采信），表单可覆盖（手动修正通道）
    """
    try:
        result = svc.import_zip(db, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    meta = svc.extract_meta(result["data"])
    # 表单覆盖派生值
    if name and name.strip():
        meta["name"] = name.strip()
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
    # 作者：表单（JSON 数组字符串）优先，回落 MD 派生；写入时经 users 表补全昵称/部门
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
        name=meta["name"],
        desc=meta["desc"] or None,
        author=author_json,
        icon=icon_rel,
        usage=usage_val,
        cover=meta["cover"],
        is_default=bool(default_val) if default_val is not None else False,
        file_path=svc.rel_path(result["slug"]),
        source_md_path=result["source_md_rel"],
        source_zip_path=result["source_zip_rel"],
        skill_zip_path=result["skill_zip_rel"],
        skill_name=result["skill_name"],
        file_size=len(content),
        created_by=account,
        updated_by=account,
        is_deleted=0,
    )
    if row.is_default:
        _clear_default(db, row.slug)
    db.add(row)
    db.flush()
    return row


def _reupload_zip(
    db: Session,
    request: Request,
    slug: str,
    content: bytes,
    filename: Optional[str],
) -> DesignSystem:
    """zip 重传覆盖（PUT /{slug}/json 与分片 complete 重传模式共用；调用方负责 commit/日志）。

    - 内容替换：design-system.json / source.zip / source.md / 附件（DESIGN.md 同级任意 .zip，
      保留原文件名落盘） / assets；旧附件与新附件名不同（或新包无附件）时按 DB 列清理旧文件
    - name 跟随新 MD；usage/封面/图标/作者/描述/默认标记保留（管理字段不被覆盖）
    - MD id 变化只更新 source_slug 并记录日志（slug 与落盘目录不动）
    """
    row = _get_by_slug(db, slug)
    try:
        result = svc.import_zip(
            db, content, existing_slug=slug, old_skill_zip_rel=row.skill_zip_path
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    derived = svc.extract_meta(result["data"])
    source_slug_changed = result["source_slug"] != (row.source_slug or "")
    row.source_slug = result["source_slug"]
    row.name = derived["name"]
    row.file_size = len(content)
    row.file_path = svc.rel_path(slug)
    row.source_md_path = result["source_md_rel"]
    row.source_zip_path = result["source_zip_rel"]
    row.skill_zip_path = result["skill_zip_rel"]
    row.skill_name = result["skill_name"]
    account, _ = get_operator(request)
    row.updated_by = account
    _log(db, request, "reupload", row, {
        "file": filename,
        "size": len(content),
        **({"source_slug": row.source_slug} if source_slug_changed else {}),
    })
    return row


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


# ─────────────────────────── 5. zip 重传覆盖 ───────────────────────────

@router.put("/{slug}/json")
async def put_design_system_json(
    slug: str,
    request: Request,
    file: UploadFile = File(..., description="新 zip 包（octo-design-zip/1 格式，≤200MB）"),
    db: Session = Depends(get_db),
):
    """重传覆盖：zip 解析后替换全部内容文件；name 跟随新 MD，管理字段保留。

    （大文件由前端走分片 complete 的 slug 重传模式，语义与本接口一致）
    """
    _check_zip_ext(file.filename)
    content = await file.read()
    if len(content) > dzip.MAX_ZIP_BYTES:
        raise HTTPException(status_code=413, detail="zip 包超过 %dMB 上限" % (dzip.MAX_ZIP_BYTES // 1024 // 1024))
    row = _reupload_zip(db, request, slug, content, file.filename)
    db.commit()
    db.refresh(row)
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))


# ─────────────────────────── 7. 调用量自增 ───────────────────────────

def _increment_with_event(slug: str, request: Request, db: Session, column: str, event_type: str):
    """usage / views 自增 + 打点事件写入（同一事务，保证统计口径与累计列一致）。

    - 身份来自 X-User-Data（AuthMiddleware 解密），写入前经 resolve_user_info 三级兜底完整化
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
        raise HTTPException(status_code=404, detail="设计系统「%s」不存在" % slug)

    # 身份完整化（可能含 getAccount 外部查询）放在事务性写入之前，失败降级不丢打点
    info = resolve_user_info(db, get_operator(request))
    account, nick_name, dept1, dept2, dept3, dept4 = snapshot_fields(info)

    db.add(DsUsageEvent(
        slug=slug, event_type=event_type,
        account=account or None, nick_name=nick_name or None,
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
    db.commit()
    db.refresh(row)
    return row


@router.post("/{slug}/usage")
def increment_usage(slug: str, request: Request, db: Session = Depends(get_db)):
    """使用方（如 Octo Design）显式调用，usage += 1，同时写入打点事件（建议携带 X-User-Data）。"""
    row = _increment_with_event(slug, request, db, "usage", "usage")
    return {"slug": slug, "usage": row.usage}


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
