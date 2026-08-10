import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


def resolve_display_names(db: Session, accounts: List[str]) -> dict:
    """批量解析 account → 'nickName account' 显示字符串。

    查不到的 account 原样返回（兜底）。
    """
    if not accounts:
        return {}
    try:
        rows = (
            db.query(User.account, User.nick_name)
            .filter(User.account.in_(accounts))
            .all()
        )
        return {
            acc: (f"{nick} {acc}" if nick else acc)
            for acc, nick in rows
        }
    except Exception as e:
        logger.warning("resolve_display_names 失败: %s", e)
        return {}


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
            existing.deptcode = user_data.get("deptcode", existing.deptcode)
            existing.nick_name = user_data.get("nickName", existing.nick_name)
            existing.role_id = user_data.get("roleId", existing.role_id)
            existing.roles = user_data.get("roles", existing.roles)
            existing.uid = user_data.get("uid", existing.uid)
            existing.uuid = user_data.get("uuid", existing.uuid)
            existing.last_login_at = now
        else:
            db.add(User(
                account=account,
                dept=user_data.get("dept", ""),
                deptcode=user_data.get("deptcode", ""),
                nick_name=user_data.get("nickName", ""),
                role_id=user_data.get("roleId", ""),
                roles=user_data.get("roles", ""),
                uid=user_data.get("uid", ""),
                uuid=user_data.get("uuid", ""),
                last_login_at=now,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("upsert 用户失败: account=%s, error=%s", account, e)
