"""
全量请求访问日志中间件

每个 HTTP 请求一行日志，写入 logs/requests.txt（按天轮转，浏览器可经 /logs/requests.txt 查看）：
- 常规请求一行 INFO：method path?query status 耗时ms ip user req
- 耗时超过 SLOW_REQUEST_MS 的请求打 [SLOW] 前缀（WARNING）
- 响应头带 X-Request-ID，用户报障时用于对账

跳过噪声：/static、/logs、/health、/docs、/redoc、/openapi.json 及 OPTIONS 预检。
纯 ASGI 中间件实现（与 SearchLogMiddleware 一致，不用 BaseHTTPMiddleware）。
"""

import logging
import time
import uuid
from urllib.parse import unquote

from app.config import settings

logger = logging.getLogger("request_log")

_SKIP_PREFIXES = ("/static", "/logs")
_SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}
_QUERY_MAX_LEN = 200


class AccessLogMiddleware:
    """全量请求访问日志：注册在最外层，耗时统计含认证全链路。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        if not settings.ACCESS_LOG_ENABLED:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        if method == "OPTIONS" or path in _SKIP_PATHS or path.startswith(_SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:8]
        query = unquote(scope.get("query_string", b"").decode("latin-1", errors="replace"))
        if len(query) > _QUERY_MAX_LEN:
            query = query[:_QUERY_MAX_LEN] + "..."
        ip = self._client_ip(scope)

        http_status = {"status_code": 200}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                http_status["status_code"] = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-request-id", request_id.encode()),
                ]
            await send(message)

        start = time.monotonic()
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._log(request_id, method, path, query, 500,
                      int((time.monotonic() - start) * 1000), ip, self._operator(scope))
            raise

        self._log(request_id, method, path, query, http_status["status_code"],
                  int((time.monotonic() - start) * 1000), ip, self._operator(scope))

    @staticmethod
    def _operator(scope) -> str:
        """AuthMiddleware 解密后写入 scope.state 的操作人，响应结束后读取。"""
        operator = (scope.get("state") or {}).get("operator")
        return operator.account if operator else "-"

    @staticmethod
    def _client_ip(scope) -> str:
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        xff = headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        xri = headers.get("x-real-ip")
        if xri:
            return xri.strip()
        client = scope.get("client")
        return client[0] if client else "-"

    @staticmethod
    def _log(request_id, method, path, query, status, duration_ms, ip, user):
        line = f"{method} {path}{('?' + query) if query else ''} {status} {duration_ms}ms ip={ip} user={user} req={request_id}"
        if duration_ms >= settings.SLOW_REQUEST_MS:
            logger.warning("[SLOW] %s", line)
        else:
            logger.info("%s", line)
