"""设计系统白名单业务逻辑（独立于原 whitelist_service，零共享）"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.ds_whitelist import DsWhitelistAccount


def get_accounts(
    db: Session,
    is_active: Optional[int] = None,
    search: Optional[str] = None,
) -> List[DsWhitelistAccount]:
    query = db.query(DsWhitelistAccount)
    if is_active is not None:
        query = query.filter(DsWhitelistAccount.is_active == is_active)
    if search:
        like = f"%{search}%"
        query = query.filter(
            DsWhitelistAccount.account.ilike(like) | DsWhitelistAccount.nick_name.ilike(like)
        )
    return query.order_by(DsWhitelistAccount.id.asc()).all()


def get_account(db: Session, account: str) -> Optional[DsWhitelistAccount]:
    return db.query(DsWhitelistAccount).filter(DsWhitelistAccount.account == account).first()


def get_account_by_id(db: Session, pk: int) -> Optional[DsWhitelistAccount]:
    return db.query(DsWhitelistAccount).filter(DsWhitelistAccount.id == pk).first()


def create_account(
    db: Session,
    account: str,
    nick_name: Optional[str] = None,
    remark: Optional[str] = None,
    role: str = "admin",
) -> DsWhitelistAccount:
    if not account or not account.strip():
        raise ValueError("account 不能为空")
    account = account.strip()
    if get_account(db, account):
        raise ValueError(f"账号 {account} 已存在")
    if role not in ("super", "admin"):
        raise ValueError("role 仅支持 super / admin")
    item = DsWhitelistAccount(account=account, nick_name=nick_name, remark=remark, role=role)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_account(
    db: Session,
    item: DsWhitelistAccount,
    nick_name: Optional[str] = None,
    remark: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[int] = None,
) -> DsWhitelistAccount:
    if nick_name is not None:
        item.nick_name = nick_name
    if remark is not None:
        item.remark = remark
    if role is not None:
        if role not in ("super", "admin"):
            raise ValueError("role 仅支持 super / admin")
        item.role = role
    if is_active is not None:
        item.is_active = is_active
    db.commit()
    db.refresh(item)
    return item


def soft_delete(db: Session, item: DsWhitelistAccount) -> None:
    item.is_active = 0
    db.commit()
