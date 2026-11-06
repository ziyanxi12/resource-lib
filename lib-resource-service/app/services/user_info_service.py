"""设计系统打点：事件写入前的「用户信息完整化」服务。

三级兜底链（保证事件快照尽量完整，同时绝不因兜底失败丢打点）：
    ① X-User-Data 解密结果（AuthMiddleware → OperatorInfo，零开销快路径）
    ② 缺 nickName / dept 时 → 查 users 表（AuthMiddleware 每次请求异步 upsert 的缓存）
    ③ 仍缺 → 调 getAccount 人员服务按 account 精确补全，成功则回写 users 表
              （同一账号此后永远命中本地表，外部服务最多查 1 次/人）
    全部失败 → 用手头信息降级写事件（account 保证有），缺项留空。
"""

import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

# getAccount 短超时：人员服务抖动不能拖慢/拖挂打点接口
_GETACCOUNT_TIMEOUT = 2.0


def _clean_dept(dept) -> list:
    """部门输入（list/str）→ 干净的字符串数组。"""
    if isinstance(dept, list):
        return [str(d).strip() for d in dept if str(d).strip()]
    if isinstance(dept, str) and dept.strip():
        return [dept.strip()]
    return []


def getaccount_lookup(account: str) -> Optional[dict]:
    """按 account 精确查询 getAccount 人员服务。

    返回 {account, nickName, dept: [...]}；未配置 / 超时 / 查不到 / 格式异常 → None（静默降级）。
    """
    if not account or not settings.GET_ACCOUNT_API_URL:
        return None
    try:
        resp = httpx.get(
            "%s?keyword=%s" % (settings.GET_ACCOUNT_API_URL, account),
            timeout=_GETACCOUNT_TIMEOUT,
            trust_env=False,
            headers={"uiplusToken": settings.GET_ACCOUNT_API_TOKEN},
        )
        resp.raise_for_status()
        # 响应格式：{"content": {"<keyword>": [ {account, nickName, dept...} ... ]}, "errorCode": 0}
        content = (resp.json() or {}).get("content") or {}
        for users in content.values():
            if not isinstance(users, list):
                continue
            for u in users:
                if isinstance(u, dict) and str(u.get("account", "")).strip() == account:
                    return {
                        "account": account,
                        "nickName": str(u.get("nickName", "")).strip(),
                        "dept": _clean_dept(u.get("dept")),
                    }
    except Exception as e:  # noqa: BLE001
        logger.warning("getaccount_lookup(%s) 失败（降级）: %s", account, e)
    return None


def _is_complete(account: str, nick_name: str, dept: list) -> bool:
    return bool(account) and bool(nick_name) and bool(dept)


def resolve_user_info(db: Session, op) -> dict:
    """OperatorInfo → 完整用户信息 {account, nick_name, dept: [...]}。

    合并语义：空值不覆盖非空值（X-User-Data 带了就用，缺的往下兜底）。
    op 为 None / 匿名（account 为空或 unknown）→ 返回全空 dict（事件归「未知」）。
    """
    account = str(getattr(op, "account", "") or "").strip()
    if not account or account == "unknown":
        return {"account": "", "nick_name": "", "dept": []}

    nick = str(getattr(op, "nick_name", "") or "").strip()
    if nick == "unknown":
        nick = ""
    dept = _clean_dept(getattr(op, "dept", None))

    # ② users 表兜底（AuthMiddleware 平时 upsert 的缓存，单行索引查询）
    if not _is_complete(account, nick, dept):
        try:
            from app.models.user import User

            row = db.query(User.nick_name, User.dept).filter(User.account == account).first()
            if row:
                nick = nick or (row.nick_name or "").strip()
                if not dept:
                    dept = _clean_dept(row.dept)
        except Exception as e:  # noqa: BLE001
            logger.warning("resolve_user_info 查 users 表失败: %s", e)

    # ③ getAccount 终极兜底 + 回写 users 表（后续命中本地）
    if not _is_complete(account, nick, dept):
        hit = getaccount_lookup(account)
        if hit:
            nick = nick or hit["nickName"]
            if not dept:
                dept = hit["dept"]
            try:
                from app.services.user_service import upsert_user

                # upsert_user 是「有值才传」语义（None 会覆盖存量），只带查到的字段
                payload = {"account": account}
                if hit["nickName"]:
                    payload["nickName"] = hit["nickName"]
                if hit["dept"]:
                    payload["dept"] = hit["dept"]
                upsert_user(db, payload)
                db.commit()
            except Exception as e:  # noqa: BLE001
                logger.warning("resolve_user_info 回写 users 表失败: %s", e)

    return {"account": account, "nick_name": nick, "dept": dept}


def snapshot_fields(info: dict):
    """完整化结果 → 事件表快照字段 (account, nick_name, dept1, dept2, dept3, dept4)。

    需求口径：dept[1]..dept[4] = 部门数组的**下标 1~4**（dept[0] 是公司名「华为」，
    不属于层级也不参与统计——否则一层部门占比恒为 100%）。数组不足的层为空。
    """
    dept = (info.get("dept") or [])[1:5]
    dept = (list(dept) + ["", "", "", ""])[:4]
    return (
        (info.get("account") or "").strip(),
        (info.get("nick_name") or "").strip(),
        dept[0] or None, dept[1] or None, dept[2] or None, dept[3] or None,
    )
