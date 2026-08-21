from datetime import datetime
import logging
from typing import List, Optional

import httpx
from fastapi import Request
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


def _mock_search_users(keyword: str) -> List[dict]:
    """模拟用户搜索数据"""
    pool = [
        {"userID": "u001", "account": "guest", "nickName": "访客用户", "dept": ["技术部"]},
        {"userID": "u002", "account": "admin", "nickName": "管理员", "dept": ["平台部"]},
        {"userID": "u003", "account": "zhangsan", "nickName": "张三", "dept": ["设计部", "创意中心"]},
        {"userID": "u004", "account": "lisi", "nickName": "李四", "dept": ["前端开发部"]},
        {"userID": "u005", "account": "wangwu", "nickName": "王五", "dept": ["后端开发部"]},
    ]
    kw = keyword.lower()
    return [u for u in pool if kw in u["account"].lower() or kw in u["nickName"].lower()]


def search_users(keyword: str, request: Request) -> List[dict]:
    """按关键词搜索用户。USE_MOCK=true 返回模拟数据，否则调外部 API（转发 cookie + uiplusToken）。"""
    if not keyword or not keyword.strip():
        return []
    keyword = keyword.strip()

    if settings.USE_MOCK:
        logger.info("search_users: keyword=%s, USE_MOCK=true → mock", keyword)
        return _mock_search_users(keyword)

    if not settings.USER_SEARCH_API_URL:
        logger.warning("search_users: USER_SEARCH_API_URL 未配置，返回空")
        return []

    try:
        uiplustoken = request.headers.get("uiplusToken", "")
        cookie_keys = list(request.cookies.keys())
        logger.info(
            "search_users: keyword=%s, uiplusToken=%s, cookie_keys=%s",
            keyword,
            f"present(len={len(uiplustoken)})" if uiplustoken else "missing",
            cookie_keys,
        )

        api_url = f"{settings.USER_SEARCH_API_URL}?keyword={keyword}"
        logger.debug("search_users: 调用外部 API: %s", api_url)

        resp = httpx.get(
            api_url,
            timeout=6,
            trust_env=False,
            cookies=request.cookies,
            headers={"uiplusToken": uiplustoken},
        )
        logger.info(
            "search_users: 外部 API 返回: status=%s, body_len=%s",
            resp.status_code,
            len(resp.content),
        )
        resp.raise_for_status()

        content = resp.json().get("content", {})
        for _, users in content.items():
            result = users if isinstance(users, list) else []
            logger.info("search_users: 解析成功, users_count=%d", len(result))
            return result
        logger.warning("search_users: content 为空或格式不符: %s", str(content)[:200])
        return []
    except Exception as e:
        logger.warning("search_users: 外部 API 搜索用户失败: keyword=%s, error=%s", keyword, e)
        return []


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


def get_user_by_account(db: Session, account: str) -> Optional[User]:
    """按 account 精确查 users 表（登录自动 upsert 的记录）。未命中返回 None，不报错。"""
    if not account:
        return None
    return db.query(User).filter(User.account == account).first()


def list_users(
    db: Session,
    search: Optional[str] = None,
    whitelisted: Optional[int] = None,
) -> List[User]:
    """列出用户（含是否在白名单标记）。按最后登录时间倒序。

    whitelisted: None=全部, 1=仅在启用白名单中, 0=未加入
    """
    query = db.query(User)
    if search:
        like = f"%{search}%"
        query = query.filter(User.account.ilike(like) | User.nick_name.ilike(like))

    if whitelisted is not None:
        from app.models.whitelist_account import WhitelistAccount

        enabled = (
            db.query(WhitelistAccount.account)
            .filter(WhitelistAccount.is_active == 1)
            .subquery()
        )
        if whitelisted == 1:
            query = query.filter(User.account.in_(enabled))
        elif whitelisted == 0:
            query = query.filter(~User.account.in_(enabled))

    return query.order_by(User.last_login_at.desc(), User.id.desc()).all()


def get_whitelisted_account_set(db: Session) -> set:
    """返回所有启用白名单账号集合（供序列化标记用）"""
    from app.models.whitelist_account import WhitelistAccount

    rows = (
        db.query(WhitelistAccount.account)
        .filter(WhitelistAccount.is_active == 1)
        .all()
    )
    return {r.account for r in rows}


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
