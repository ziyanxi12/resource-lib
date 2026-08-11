"""
认证中间件：解密 X-User-Data header → upsert 到 users 表 → 存入 request.state

纯 ASGI 中间件，不阻塞请求。upsert 在独立线程执行。
"""

import logging
from concurrent.futures import ThreadPoolExecutor

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

        path = scope.get("path", "")
        if path.startswith("/api/sources/") and path.endswith("/import"):
            logger.info("[AuthMiddleware] import 请求: path=%s, has_x-user-data=%s, header_len=%s",
                        path, bool(encrypted), len(encrypted) if encrypted else 0)

        operator = None
        if encrypted:
            try:
                user_data = decrypt_user_data(encrypted)
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

        scope.setdefault("state", {})["operator"] = operator
        await self.app(scope, receive, send)
