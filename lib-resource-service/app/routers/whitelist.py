"""
访问白名单管理路由
GET    /api/whitelist            列表（?is_active=&search=）
POST   /api/whitelist            新增
POST   /api/whitelist/batch      批量新增
PUT    /api/whitelist/{id}       更新昵称/备注/状态
DELETE /api/whitelist/{id}       删除（软）
GET    /api/whitelist/check      前端入口校验（?account= 或 X-User-Data 解密账号）
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.whitelist import WhitelistCreate, WhitelistBatchCreate, WhitelistUpdate
from app.services import operation_log_service, whitelist_service
from app.services.operator import get_operator

router = APIRouter(prefix="/api/whitelist", tags=["访问白名单"])


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


@router.get("")
def list_accounts(
    is_active: Optional[int] = Query(None, description="1=启用 0=禁用"),
    search: Optional[str] = Query(None, description="按账号/昵称模糊搜索"),
    db: Session = Depends(get_db),
):
    items = whitelist_service.get_accounts(db, is_active=is_active, search=search)
    return {"items": [_fmt(i) for i in items]}


@router.get("/check")
def check_whitelist(
    request: Request,
    account: Optional[str] = Query(None, description="账号（未带 X-User-Data 时回退）"),
    db: Session = Depends(get_db),
):
    """前端入口校验：优先用解密后的登录账号，否则用 query 参数。返回 allowed/role/nick_name。"""
    op = get_operator(request)
    real_account = op.account if op and op.account != "unknown" else None
    checked_account = real_account or account

    item = whitelist_service.get_account(db, checked_account) if checked_account else None
    in_whitelist = bool(item) and item.is_active == 1

    if getattr(settings, "WHITELIST_ENABLED", False):
        allowed = in_whitelist
    else:
        allowed = True

    role = item.role if item else None
    nick_name = item.nick_name if item else None
    return {"allowed": allowed, "account": checked_account, "nick_name": nick_name, "role": role}


@router.post("")
def create_account(body: WhitelistCreate, request: Request, db: Session = Depends(get_db)):
    try:
        item = whitelist_service.create_account(
            db,
            account=body.account,
            nick_name=body.nick_name,
            remark=body.remark,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    op_account, op_name = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=op_name,
        operator_account=op_account,
        action="create",
        target_type="whitelist",
        target_id=item.id,
        target_name=item.account,
    )
    return _fmt(item)


@router.post("/batch")
def batch_create(body: WhitelistBatchCreate, request: Request, db: Session = Depends(get_db)):
    accounts = [item.model_dump(exclude_unset=True) for item in body.accounts]
    if not accounts:
        raise HTTPException(status_code=400, detail="accounts is required")

    result = whitelist_service.batch_create(db, accounts)

    op_account, op_name = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=op_name,
        operator_account=op_account,
        action="batch_create",
        target_type="whitelist",
        target_name=f"批量新增白名单",
        detail={"created": result["created"], "skipped": result["skipped"]},
    )
    return result


@router.put("/{pk}")
def update_account(pk: int, body: WhitelistUpdate, request: Request, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    item = whitelist_service.update_account(db, pk, data)
    if not item:
        raise HTTPException(status_code=404, detail="白名单账号不存在")

    op_account, op_name = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=op_name,
        operator_account=op_account,
        action="update",
        target_type="whitelist",
        target_id=item.id,
        target_name=item.account,
        detail=data,
    )
    return _fmt(item)


@router.delete("/{pk}")
def delete_account(pk: int, request: Request, db: Session = Depends(get_db)):
    item = whitelist_service.get_account_by_id(db, pk)
    if not item:
        raise HTTPException(status_code=404, detail="白名单账号不存在")
    whitelist_service.delete_account(db, pk)

    op_account, op_name = get_operator(request)
    operation_log_service.create_log(
        db,
        operator=op_name,
        operator_account=op_account,
        action="delete",
        target_type="whitelist",
        target_id=item.id,
        target_name=item.account,
    )
    return {"message": "已删除"}