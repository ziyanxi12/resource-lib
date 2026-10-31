"""设计系统管理路由（对齐 requirement/api.md 契约）

- 列表（api1）/ 上传 / 详情 JSON / 改 meta / 重传覆盖 / 软删
- 存储：FILE_ROOT_DIR/design-systems/{slug}/design-system.json（经 /static 对外可访问）
- 操作日志复用 operation_log_service；操作人来自 AuthMiddleware 解密的 X-User-Data
"""

import logging
import os

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.design_system import DesignSystem
from app.models.operation_log import OperationLog
from app.services import design_system_service as svc
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


# ─────────────────────────── 1. 列表（api1） ───────────────────────────

@router.get("")
def list_design_systems(
    search: Optional[str] = Query(None, description="按名称/slug/作者模糊搜索"),
    db: Session = Depends(get_db),
):
    q = db.query(DesignSystem).filter(DesignSystem.is_deleted == 0)
    if search and search.strip():
        kw = "%%%s%%" % search.strip()
        q = q.filter(
            or_(
                DesignSystem.name.ilike(kw),
                DesignSystem.slug.ilike(kw),
                DesignSystem.author.ilike(kw),
            )
        )
    rows = q.order_by(DesignSystem.is_default.desc(), DesignSystem.slug.asc()).all()
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


# ─────────────────────────── 2. 上传 ───────────────────────────

@router.post("")
async def create_design_system(
    request: Request,
    file: UploadFile = File(..., description="design-system.json（≤10MB）"),
    name: Optional[str] = Form(None),
    desc: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    usage: Optional[str] = Form(None),
    cover: Optional[str] = Form(None),
    default: Optional[str] = Form(None),
    cover_file: Optional[UploadFile] = File(None, description="可选封面图片（jpg/png/webp ≤2MB）"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > svc.MAX_JSON_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 10MB 上限")

    data, errors = svc.parse_upload(content)
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))

    meta = svc.extract_meta(data)
    if db.query(DesignSystem).filter(DesignSystem.slug == meta["slug"], DesignSystem.is_deleted == 0).first():
        raise HTTPException(status_code=409, detail="slug「%s」已存在；如需更新内容，请在列表页对该系统使用「重传」" % meta["slug"])

    # 表单覆盖派生值
    if name and name.strip():
        meta["name"] = name.strip()
    if desc is not None and desc != "":
        meta["desc"] = desc
    if author and author.strip():
        meta["author"] = author.strip()
    try:
        usage_val = svc.parse_form_int(usage)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if usage_val is not None:
        meta["usage"] = usage_val
    if cover:
        meta["cover"] = svc.normalize_cover(cover)
    # 自定义封面图片：上传则覆盖内置名（文件名固定 {slug}.{ext}）
    if cover_file is not None:
        cover_content = await cover_file.read()
        try:
            ext = svc.validate_cover_upload(cover_file.filename, cover_content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        meta["cover"] = svc.save_cover_file(meta["slug"], ext, cover_content)
    default_val = svc.parse_form_bool(default)
    if default_val is not None:
        meta["default"] = default_val

    svc.save_json_file(meta["slug"], data, len(content))
    account, _op_name = get_operator(request)
    row = DesignSystem(
        slug=meta["slug"],
        name=meta["name"],
        desc=meta["desc"] or None,
        author=meta["author"] or None,
        usage=meta["usage"],
        cover=meta["cover"],
        is_default=bool(meta["default"]),
        file_path=svc.rel_path(meta["slug"]),
        file_size=len(content),
        created_by=account,
        updated_by=account,
    )
    if row.is_default:
        _clear_default(db, row.slug)
    db.add(row)
    db.commit()
    db.refresh(row)
    _log(db, request, "create", row, {"slug": row.slug, "file": file.filename})
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))


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
    author: Optional[str] = Form(None),
    usage: Optional[str] = Form(None),
    default: Optional[str] = Form(None),
    cover_file: Optional[UploadFile] = File(None, description="可选新封面（jpg/png/webp ≤2MB）；不上传则保留现有封面"),
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
        row.author = author
        detail["author"] = author
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


# ─────────────────────────── 5. 重传覆盖 ───────────────────────────

@router.put("/{slug}/json")
async def put_design_system_json(
    slug: str,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    row = _get_by_slug(db, slug)
    content = await file.read()
    if len(content) > svc.MAX_JSON_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 10MB 上限")

    data, errors = svc.parse_upload(content)
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))

    derived = svc.extract_meta(data)
    if derived["slug"] != slug:
        raise HTTPException(status_code=400, detail="JSON 的 id「%s」与目标系统「%s」不一致" % (derived["slug"], slug))

    # 内容替换：name 跟随新 JSON；封面保留现有（避免自定义封面被 JSON 的 cover 重置）；
    # 作者/调用量/描述/默认标记保留
    svc.save_json_file(slug, data, len(content))
    row.name = derived["name"]
    row.file_size = len(content)
    account, _ = get_operator(request)
    row.updated_by = account
    db.commit()
    db.refresh(row)
    _log(db, request, "reupload", row, {"file": file.filename, "size": len(content)})
    return svc.format_item(row, svc.resolve_display_map(db, [row.created_by, row.updated_by]))


# ─────────────────────────── 7. 调用量自增 ───────────────────────────

@router.post("/{slug}/usage")
def increment_usage(slug: str, db: Session = Depends(get_db)):
    """展示端打开/使用该设计系统时调用，usage += delta（默认 1）。

    说明：
    - 高频调用，不写操作日志、不改动 updated_at（那是内容/管理字段的更新时间）
    - SQL 端自增（usage = usage + delta），避免并发读改写丢失
    """
    row = (
        db.query(DesignSystem)
        .filter(DesignSystem.slug == slug, DesignSystem.is_deleted == 0)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="设计系统「%s」不存在" % slug)

    db.query(DesignSystem).filter(
        DesignSystem.slug == slug, DesignSystem.is_deleted == 0
    ).update(
        {
            "usage": DesignSystem.usage + 1,
            # 显式提供 updated_at 覆盖列级 onupdate，保持其语义不变
            "updated_at": DesignSystem.updated_at,
        },
        synchronize_session=False,
    )
    db.commit()
    db.refresh(row)
    return {"slug": slug, "usage": row.usage}


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
