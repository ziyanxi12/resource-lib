"""
用户查询路由（只读）
GET /api/users            用户列表（?search=&whitelisted=）
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["用户"])


def _fmt_user(user, whitelist_set: set) -> dict:
    return {
        "id": user.id,
        "account": user.account,
        "nick_name": user.nick_name,
        "dept": user.dept,
        "dept_code": user.dept_code,
        "role_id": user.role_id,
        "roles": user.roles,
        "uid": user.uid,
        "user_id": user.user_id,
        "last_login_at": int(user.last_login_at.timestamp() * 1000) if user.last_login_at else None,
        "created_at": int(user.created_at.timestamp() * 1000) if user.created_at else None,
        "updated_at": int(user.updated_at.timestamp() * 1000) if user.updated_at else None,
        "is_whitelisted": user.account in whitelist_set,
    }


@router.get("")
def list_users(
    search: Optional[str] = Query(None, description="按账号/昵称模糊搜索"),
    whitelisted: Optional[int] = Query(None, description="1=仅已加白名单 0=仅未加白名单"),
    db: Session = Depends(get_db),
):
    users = user_service.list_users(db, search=search, whitelisted=whitelisted)
    whitelist_set = user_service.get_whitelisted_account_set(db)
    return {"items": [_fmt_user(u, whitelist_set) for u in users]}