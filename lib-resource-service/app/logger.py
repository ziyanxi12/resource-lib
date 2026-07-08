import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler


class _DebugOnlyFilter(logging.Filter):
    """只放行 DEBUG 级别，INFO 及以上交给 app.txt。"""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.DEBUG


def setup_logging(log_dir: str, log_level: str = "INFO") -> None:
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # INFO / WARNING / ERROR / CRITICAL → app.txt，保留 30 天
    app_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.txt"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.namer = _namer
    app_handler.setFormatter(fmt)

    # DEBUG only → debug.txt（含 httpx/httpcore 请求明细），保留 7 天
    debug_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "debug.txt"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(_DebugOnlyFilter())
    debug_handler.namer = _namer
    debug_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.addHandler(app_handler)
    root.addHandler(debug_handler)
    
    # 抑制第三方库的 DEBUG/INFO 日志，只保留 WARNING 以上
    for lib in ["httpx", "httpcore", "httpx._client", "httpcore._backends", "hpack", "hpack.hpack"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


def _namer(name: str) -> str:
    # TimedRotatingFileHandler 默认生成 app.txt.2026-06-27，改为 app-2026-06-27.txt
    m = re.match(r"^(.*?)\.txt\.(\d{4}-\d{2}-\d{2})$", name)
    return f"{m.group(1)}-{m.group(2)}.txt" if m else name
