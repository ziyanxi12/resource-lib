import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler


def setup_logging(log_dir: str, log_level: str = "INFO") -> None:
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.txt"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.namer = _namer
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.addHandler(handler)


def _namer(name: str) -> str:
    # TimedRotatingFileHandler 默认生成 app.txt.2026-06-27，改为 app-2026-06-27.txt
    m = re.match(r"^(.*?)\.txt\.(\d{4}-\d{2}-\d{2})$", name)
    return f"{m.group(1)}-{m.group(2)}.txt" if m else name
