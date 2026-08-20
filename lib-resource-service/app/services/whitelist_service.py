import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.whitelist_account import WhitelistAccount

logger = logging.getLogger(__name__)


def get_accounts(
    db: Session,
    is_active: Optional[int] = None,
    search: Optional[str] = None,
) -> List[WhitelistAccount]:
    query = db.query(WhitelistAccount)
    if is_active is not None:
        query = query.filter(WhitelistAccount.is_active == is_active)
    if search:
        like = f"%{search}%"
        query = query.filter(
            WhitelistAccount.account.ilike(like) | WhitelistAccount.nick_name.ilike(like)
        )
    return query.order_by(WhitelistAccount.created_at.desc()).all()


def get_account(db: Session, account: str) -> Optional[WhitelistAccount]:
    return db.query(WhitelistAccount).filter(WhitelistAccount.account == account).first()


def get_account_by_id(db: Session, pk: int) -> Optional[WhitelistAccount]:
    return db.query(WhitelistAccount).filter(WhitelistAccount.id == pk).first()


def create_account(
    db: Session,
    account: str,
    nick_name: Optional[str] = None,
    remark: Optional[str] = None,
) -> WhitelistAccount:
    if not account or not account.strip():
        raise ValueError("account is required")
    account = account.strip()
    if get_account(db, account):
        raise ValueError(f"账号已存在: {account}")

    nick = (nick_name or "").strip() or None
    if not nick:
        nick = _lookup_nick_name(db, account)

    item = WhitelistAccount(
        account=account,
        nick_name=nick,
        remark=remark,
        role="admin",
        is_active=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _lookup_nick_name(db: Session, account: str) -> Optional[str]:
    """从 users 表按 account 查昵称，查不到返回 None（不报错，不阻塞）。"""
    try:
        from app.services.user_service import get_user_by_account
        u = get_user_by_account(db, account)
        return (u.nick_name or None) if u else None
    except Exception:
        return None


def batch_create(db: Session, accounts: list) -> dict:
    """批量新增。跳过空账号与已存在账号。返回 {created, skipped}"""
    created = 0
    skipped = 0
    for raw in accounts:
        account = (raw.get("account") or "").strip() if isinstance(raw, dict) else str(raw).strip()
        if not account:
            continue
        try:
            create_account(
                db,
                account=account,
                nick_name=(raw.get("nick_name") if isinstance(raw, dict) else None),
                remark=(raw.get("remark") if isinstance(raw, dict) else None),
            )
            created += 1
        except ValueError:
            skipped += 1
    return {"created": created, "skipped": skipped}


def update_account(db: Session, pk: int, data: dict) -> Optional[WhitelistAccount]:
    item = get_account_by_id(db, pk)
    if not item:
        return None
    for key in ("nick_name", "remark", "is_active", "role"):
        if key in data:
            setattr(item, key, data[key])
    db.commit()
    db.refresh(item)
    return item


def delete_account(db: Session, pk: int) -> bool:
    item = get_account_by_id(db, pk)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def is_whitelisted(db: Session, account: Optional[str]) -> bool:
    if not account or account == "unknown":
        return False
    item = db.query(WhitelistAccount).filter(
        WhitelistAccount.account == account,
        WhitelistAccount.is_active == 1,
    ).first()
    return item is not None


def refresh_nick_name(db: Session, pk: int) -> tuple:
    """仅当记录 nick_name 为空时，从 users 表按 account 补全。

    返回 (item, updated, message)。
    - item 为 None 表示记录不存在；
    - updated=True 表示本次补全成功；
    - nick_name 已有值则跳过（updated=False）。
    """
    item = get_account_by_id(db, pk)
    if not item:
        return (None, False, "白名单账号不存在")

    if item.nick_name:
        return (item, False, f"已有昵称（{item.nick_name}），跳过")

    nick = _lookup_nick_name(db, item.account)
    if not nick:
        return (item, False, "用户表未找到该账号，无法补全")

    item.nick_name = nick
    db.commit()
    db.refresh(item)
    return (item, True, f"已补充昵称：{nick}")