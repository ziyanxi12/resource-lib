from datetime import datetime
import logging
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


def _fetch_user_from_api(account: str) -> Optional[dict]:
    """调外部接口获取用户信息。返回含 account/nickName/dept/deptCode 的 dict，失败返回 None。"""
    if not settings.USER_INFO_API_URL:
        return None
    try:
        resp = httpx.get(
            f"{settings.USER_INFO_API_URL}?account={account}",
            timeout=10,
            trust_env=False,
        )
        resp.raise_for_status()
        content = resp.json().get("content", {})
        if not content.get("account"):
            return None
        return content
    except Exception as e:
        logger.warning("外部 API 获取用户信息失败: account=%s, error=%s", account, e)
        return None


def resolve_display_names(db: Session, accounts: List[str]) -> dict:
    """批量解析 account → 'nickName account' 显示字符串。

    DB 查不到的 account 调外部 API 补查并入库，下次直接走 DB。
    """
    if not accounts:
        return {}
    try:
        rows = (
            db.query(User.account, User.nick_name)
            .filter(User.account.in_(accounts))
            .all()
        )
        result = {
            acc: (f"{nick} {acc}" if nick else acc)
            for acc, nick in rows
        }
    except Exception as e:
        logger.warning("resolve_display_names 查询失败: %s", e)
        result = {}

    missing = [acc for acc in accounts if acc not in result]
    for acc in missing:
        fetched = _fetch_user_from_api(acc)
        if fetched:
            upsert_user(db, fetched)
            nick = fetched.get("nickName", "")
            result[acc] = f"{nick} {acc}" if nick else acc

    return result


def upsert_user(db: Session, user_data: dict) -> None:
    """以 account 为唯一键，upsert 用户信息。静默执行，失败只 warning。"""
    account = user_data.get("account")
    if not account:
        return
    try:
        existing = db.query(User).filter(User.account == account).first()
        now = datetime.now()
        if existing:
            existing.dept = user_data.get("dept", existing.dept)
            existing.dept_code = user_data.get("deptCode", existing.dept_code)
            existing.nick_name = user_data.get("nickName", existing.nick_name)
            existing.role_id = user_data.get("roleID", existing.role_id)
            existing.roles = user_data.get("roles", existing.roles)
            existing.uid = user_data.get("uid", existing.uid)
            existing.user_id = user_data.get("userID", existing.user_id)
            existing.last_login_at = now
        else:
            db.add(User(
                account=account,
                dept=user_data.get("dept", []),
                dept_code=user_data.get("deptCode", []),
                nick_name=user_data.get("nickName", ""),
                role_id=user_data.get("roleID", ""),
                roles=user_data.get("roles", []),
                uid=user_data.get("uid", 0),
                user_id=user_data.get("userID", ""),
                last_login_at=now,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("upsert 用户失败: account=%s, error=%s", account, e)
