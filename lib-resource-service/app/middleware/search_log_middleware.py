"""
向量搜索日志采集中间件

仅拦截 POST /api/vector/search，记录请求详情并异步落库。
业务接口通过 set_search_log_ctx() 写入业务字段，中间件自动补齐通用字段。

注意：必须使用纯 ASGI 中间件，不能用 BaseHTTPMiddleware。
后者在 call_next 时会复制一份子 context，导致路由里 set_search_log_ctx()
写入的 ContextVar 回不到中间件（业务字段全丢）。
"""

import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from datetime import datetime

from app.config import settings
from app.database import SessionLocal
from app.models.search_log import VectorSearchLog

logger = logging.getLogger(__name__)

_search_log_ctx: ContextVar[dict] = ContextVar("search_log_ctx", default={})

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="search-log")

TARGET_PATH = "/api/vector/search"
TARGET_METHOD = "POST"


def set_search_log_ctx(**kwargs):
    """业务接口调用，向当前请求的搜索日志上下文增量写入字段。"""
    data = {**_search_log_ctx.get(), **kwargs}
    _search_log_ctx.set(data)


def _decode_headers(raw_headers) -> dict:
    """ASGI scope 里的 headers 是 [(bytes, bytes), ...]，转成 {str_lower: str}。"""
    return {
        k.decode("latin-1").lower(): v.decode("latin-1")
        for k, v in raw_headers
    }


def _get_client_ip(scope, headers) -> str:
    xff = headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xri = headers.get("x-real-ip")
    if xri:
        return xri.strip()
    client = scope.get("client")
    return client[0] if client else ""


def _write_log(record: dict):
    """独立线程落库，失败仅告警，不影响主请求。"""
    try:
        db = SessionLocal()
        try:
            db.add(VectorSearchLog(**record))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        safe = {k: v for k, v in record.items() if k != "results"}
        logger.warning("[search_log] 落库失败: %s  record=%s", e, safe)


class SearchLogMiddleware:
    """采集 POST /api/vector/search 请求日志，其他请求直接放行。纯 ASGI 实现。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not (
            scope.get("type") == "http"
            and scope.get("method") == TARGET_METHOD
            and scope.get("path") == TARGET_PATH
        ):
            await self.app(scope, receive, send)
            return

        if not getattr(settings, "SEARCH_LOG_ENABLED", True):
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        start = time.monotonic()

        headers = _decode_headers(scope.get("headers", []))
        client_ip = _get_client_ip(scope, headers)
        app_id = headers.get("octo-vs-token") or client_ip
        user_agent = headers.get("user-agent", "")
        referer = headers.get("referer", "")

        _search_log_ctx.set({})

        http_status = {"status_code": 200}
        error_message = None
        body_chunks = []

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                http_status["status_code"] = message["status"]
                if message["status"] >= 400:
                    # 错误响应需要缓存 body 提取 error_message
                    body_chunks.append(False)
                await send(message)
            elif message["type"] == "http.response.body":
                if body_chunks and body_chunks[0] is False:
                    body_chunks[0] = True
                    body_chunks.append(message.get("body", b""))
                await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            error_message = str(e)
            http_status["status_code"] = 500
            err_body = json.dumps({"detail": str(e)}).encode()
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    (b"content-type", b"application/json"),
                ],
            })
            await send({"type": "http.response.body", "body": err_body})

        duration_ms = int((time.monotonic() - start) * 1000)
        status_code = http_status["status_code"]
        status = "success" if 200 <= status_code < 300 else "error"

        # 错误响应：从缓存的 body 提取 detail
        if error_message is None and status_code >= 400 and len(body_chunks) >= 2:
            try:
                body = b"".join(c for c in body_chunks[1:] if isinstance(c, (bytes, bytearray)))
                detail = json.loads(body).get("detail", "")
                error_message = str(detail) if detail else body.decode(errors="replace")
            except Exception:
                error_message = None

        ctx = _search_log_ctx.get()

        record = {
            "request_id": request_id,
            "api_path": TARGET_PATH,
            "resource_type": ctx.get("resource_type"),
            "search_mode": ctx.get("search_mode"),
            "response_mode": ctx.get("response_mode"),
            "top_k": ctx.get("top_k"),
            "hybrid_weight": ctx.get("hybrid_weight"),
            "query_count": ctx.get("query_count"),
            "queries": ctx.get("queries"),
            "filters": ctx.get("filters"),
            "result_count": ctx.get("result_count"),
            "result_ids": ctx.get("result_ids"),
            "top_score": ctx.get("top_score"),
            "results": ctx.get("results"),
            "status": status,
            "http_status": status_code,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "app_id": app_id,
            "user_agent": user_agent,
            "referer": referer,
            "created_at": created_at,
        }

        _executor.submit(_write_log, record)
