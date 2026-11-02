"""设计系统白名单路由（独立于原 /api/whitelist，账号与开关互不影响）

- GET    /api/design-systems/whitelist/check   登录校验（AuthGuard 调用）
- GET    /api/design-systems/whitelist         列表
- POST   /api/design-systems/whitelist         新增
- PUT    /api/design-systems/whitelist/{id}    更新昵称/备注/角色/状态
- DELETE /api/design-systems/whitelist/{id}    删除（软）
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services import ds_whitelist_service, operation_log_service
from app.services.operator import get_operator

router = APIRouter(prefix="/api/design-systems/whitelist", tags=["设计系统白名单"])


def _fmt(item) -> dict:
    return {
        "id": item.id,
        "account": item.account,
        "nick_name": item.nick_name,
        "remark": item.remark,
        "role": item.role,
        "is_active": item.is_active,
        "created_at": int(item.created_at.timestamp() * 1000) if item.created_at else None,
        "updated_at": int(item.updated_at.timestamp() * 1000) if item.updated_at else None,
    }


@router.get("/check")
def check_ds_whitelist(
    request: Request,
    account: Optional[str] = Query(None, description="账号（未带 X-User-Data 时回退）"),
    db: Session = Depends(get_db),
):
    """设计系统管理台登录校验：DS_WHITELIST_ENABLED（默认 true）只控制本模块，与原白名单开关无关。"""
    op = get_operator(request)
    real_account = op.account if op and op.account != "unknown" else None
    checked_account = real_account or account

    item = ds_whitelist_service.get_account(db, checked_account) if checked_account else None
    in_whitelist = bool(item) and item.is_active == 1

    if settings.DS_WHITELIST_ENABLED:
        allowed = in_whitelist
    else:
        allowed = True

    return {
        "allowed": allowed,
        "account": checked_account,
        "nick_name": item.nick_name if item else None,
        "role": item.role if item else None,
    }


@router.get("")
def list_accounts(
    is_active: Optional[int] = Query(None, description="1=启用 0=禁用"),
    search: Optional[str] = Query(None, description="按账号/昵称模糊搜索"),
    db: Session = Depends(get_db),
):
    items = ds_whitelist_service.get_accounts(db, is_active=is_active, search=search)
    return {"items": [_fmt(i) for i in items]}


class DsWhitelistCreate(BaseModel):
    account: str
    nick_name: Optional[str] = None
    remark: Optional[str] = None
    role: str = "admin"


@router.post("")
def create_account(body: DsWhitelistCreate, request: Request, db: Session = Depends(get_db)):
    try:
        item = ds_whitelist_service.create_account(
            db, account=body.account, nick_name=body.nick_name, remark=body.remark, role=body.role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    account_, name_ = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=name_,
        operator_account=account_,
        action="create",
        target_type="ds_whitelist",
        target_id=item.id,
        target_name=item.account,
    )
    return _fmt(item)


class DsWhitelistBatchItem(BaseModel):
    account: str
    nick_name: Optional[str] = None
    remark: Optional[str] = None
    role: str = "admin"


class DsWhitelistBatchCreate(BaseModel):
    accounts: List[DsWhitelistBatchItem]


@router.post("/batch")
def batch_create_accounts(body: DsWhitelistBatchCreate, request: Request, db: Session = Depends(get_db)):
    accounts = [item.model_dump(exclude_unset=True) for item in body.accounts]
    if not accounts:
        raise HTTPException(status_code=400, detail="accounts is required")

    result = ds_whitelist_service.batch_create(db, accounts)

    account_, name_ = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=name_,
        operator_account=account_,
        action="batch_create",
        target_type="ds_whitelist",
        target_name="批量新增设计系统白名单",
        detail={"created": result["created"], "skipped": result["skipped"]},
    )
    return result


class DsWhitelistUpdate(BaseModel):
    nick_name: Optional[str] = None
    remark: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None


@router.put("/{pk}")
def update_account(pk: int, body: DsWhitelistUpdate, request: Request, db: Session = Depends(get_db)):
    item = ds_whitelist_service.get_account_by_id(db, pk)
    if not item:
        raise HTTPException(status_code=404, detail="白名单条目不存在")
    try:
        item = ds_whitelist_service.update_account(
            db, item, nick_name=body.nick_name, remark=body.remark, role=body.role, is_active=body.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    account_, name_ = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=name_,
        operator_account=account_,
        action="update",
        target_type="ds_whitelist",
        target_id=item.id,
        target_name=item.account,
    )
    return _fmt(item)


@router.delete("/{pk}")
def delete_account(pk: int, request: Request, db: Session = Depends(get_db)):
    item = ds_whitelist_service.get_account_by_id(db, pk)
    if not item:
        raise HTTPException(status_code=404, detail="白名单条目不存在")
    ds_whitelist_service.soft_delete(db, item)
    account_, name_ = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=name_,
        operator_account=account_,
        action="delete",
        target_type="ds_whitelist",
        target_id=item.id,
        target_name=item.account,
    )
    return {"detail": "ok"}
