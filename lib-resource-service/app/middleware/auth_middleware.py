"""
认证中间件：解密 X-User-Data header → upsert 到 users 表 → 存入 request.state

纯 ASGI 中间件，不阻塞请求。upsert 在独立线程执行。

另含设计系统管理台登录过期校验：DS_LOGIN_TTL_HOURS > 0 时，/api/design-systems/* 的
管理端点要求 X-User-Data 载荷内 loginTime（毫秒时间戳）距今未超时——过期/缺失/解密失败
→ 401 {"detail": "登录已过期，请重新登录"}；展示端公开端点（GET 列表、POST views）豁免。
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.database import SessionLocal
from app.services.crypto_service import decrypt_user_data
from app.services.operator import OperatorInfo
from app.services.user_service import upsert_user

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="auth-upsert")


def _decode_headers(raw_headers) -> dict:
    """ASGI scope headers: [(bytes, bytes), ...] → {str_lower: str}"""
    return {
        k.decode("latin-1").lower(): v.decode("latin-1")
        for k, v in raw_headers
    }


def _do_upsert(user_data: dict):
    """独立线程执行 upsert，失败仅 warning。"""
    try:
        db = SessionLocal()
        try:
            upsert_user(db, user_data)
        finally:
            db.close()
    except Exception as e:
        logger.warning("auth upsert 线程异常: %s", e)


_EXPIRED_BODY = json.dumps({"detail": "登录已过期，请重新登录"}).encode("utf-8")


def _is_public_ds_endpoint(method: str, path: str) -> bool:
    """匿名可访问的公开端点：GET /api/design-systems 列表、POST /{slug}/views 打点、
    POST /api/design-systems/usage/report 免登录态调用量上报（7b，account 即身份来源）、
    POST /api/design-systems/events/refresh-identity 打点事件用户信息补全（7c，公开维护）、
    POST /api/design-systems/views/correct 预览量纠正（7d，公开维护运维通道）。"""
    if method == "GET" and path == "/api/design-systems":
        return True
    if method == "POST" and path == "/api/design-systems/usage/report":
        return True
    if method == "POST" and path == "/api/design-systems/events/refresh-identity":
        return True
    if method == "POST" and path == "/api/design-systems/views/correct":
        return True
    return (
        method == "POST"
        and path.startswith("/api/design-systems/")
        and path.endswith("/views")
    )


def _login_expired(login_time) -> bool:
    """loginTime（毫秒时间戳）距今是否超过 DS_LOGIN_TTL_HOURS；缺失/非法视为过期。"""
    if settings.DS_LOGIN_TTL_HOURS <= 0:
        return False
    if not login_time:
        return True
    try:
        age_ms = time.time() * 1000 - float(login_time)
    except (TypeError, ValueError):
        return True
    return age_ms > settings.DS_LOGIN_TTL_HOURS * 3600 * 1000


async def _send_401(send):
    """纯 ASGI 短路返回 401 JSON。AuthMiddleware 位于 CORSMiddleware 外层，需自带 CORS 头。"""
    await send({
        "type": "http.response.start",
        "status": 401,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"access-control-allow-origin", b"*"),
            (b"access-control-allow-headers", b"octo-vs-token, X-User-Data, Content-Type"),
            (b"cache-control", b"no-store"),
        ],
    })
    await send({"type": "http.response.body", "body": _EXPIRED_BODY})


class AuthMiddleware:
    """解密 X-User-Data header，存入 request.state.operator，异步 upsert users 表。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = _decode_headers(scope.get("headers", []))
        encrypted = headers.get("x-user-data")
        method = scope.get("method", "").upper()
        path = scope.get("path", "")
        if path.startswith("/api/sources/") and path.endswith("/import"):
            logger.info("[AuthMiddleware] import 请求: path=%s, has_x-user-data=%s, header_len=%s",
                        path, bool(encrypted), len(encrypted) if encrypted else 0)

        operator = None
        login_time = None
        if encrypted:
            try:
                user_data = decrypt_user_data(encrypted)
                login_time = user_data.get("loginTime")
                operator = OperatorInfo(
                    account=user_data.get("account", "unknown"),
                    dept=user_data.get("dept", []),
                    dept_code=user_data.get("deptCode", []),
                    nick_name=user_data.get("nickName", "unknown"),
                    role_id=user_data.get("roleID", ""),
                    roles=user_data.get("roles", []),
                    uid=user_data.get("uid", 0),
                    user_id=user_data.get("userID", ""),
                )
                if path.startswith("/api/sources/") and path.endswith("/import"):
                    logger.info("[AuthMiddleware] import 请求解密成功: account=%s, nick_name=%s",
                                operator.account, operator.nick_name)
                _executor.submit(_do_upsert, user_data)
            except Exception as e:
                logger.warning("[AuthMiddleware] 解密用户数据失败: %s, header_len=%s", e, len(encrypted))
        else:
            if path.startswith("/api/sources/") and path.endswith("/import"):
                logger.warning("[AuthMiddleware] import 请求缺少 X-User-Data header！path=%s", path)

        # 设计系统管理台登录过期校验：管理端点（公开端点豁免）+ 登录已过期 → 401。
        # OPTIONS 预检不带自定义头，必须放行交由 CORSMiddleware 处理。
        if (
            method != "OPTIONS"
            and path.startswith("/api/design-systems")
            and not _is_public_ds_endpoint(method, path)
            and _login_expired(login_time)
        ):
            logger.info("[AuthMiddleware] 登录过期拦截: path=%s, account=%s, ttl_hours=%s",
                        path, operator.account if operator else "-", settings.DS_LOGIN_TTL_HOURS)
            await _send_401(send)
            return

        scope.setdefault("state", {})["operator"] = operator
        await self.app(scope, receive, send)
