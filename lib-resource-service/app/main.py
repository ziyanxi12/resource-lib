"""
lib-resource-service 入口
启动后访问 http://localhost:8009/docs 查看自动生成的 API 文档
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base
from app.logger import setup_logging
from app.version import __version__
from app.enums import ResourceType
from app.models.resource import ResourceSource

# 导入所有 ORM 模型，确保 create_all 能扫描到表定义
from app.models import resource  # noqa: F401

from app.routers import resources, upload
from app.routers import vector_router, group
from app.routers import sources, init_router
from app.routers import resource_types


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时：初始化日志 + 自动建表 + 创建文件存储子目录"""
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    logger.info("lib-resource-service v%s 启动", __version__)
    Base.metadata.create_all(bind=engine)
    
    # 创建文件存储子目录
    for sub in ["component", "template", "icon", "illus", "image", "file"]:
        os.makedirs(os.path.join(settings.FILE_ROOT_DIR, sub), exist_ok=True)
    yield
    # 关闭时无需额外清理


app = FastAPI(
    title="资源库管理服务",
    description="统一管理六大类设计资源：组件集、模版、SVG、插画、图片、文件",
    version=__version__,
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,
)

# 允许前端跨域访问（开发时前端跑在不同端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各业务路由
app.include_router(resources.router)
app.include_router(upload.router)
app.include_router(vector_router.router)
app.include_router(group.router)
app.include_router(sources.router)
app.include_router(init_router.router)
app.include_router(resource_types.router)

# 静态文件服务：前端可通过 /static/{file_path} 直接访问上传文件
if os.path.exists(settings.FILE_ROOT_DIR):
    app.mount("/static", StaticFiles(directory=settings.FILE_ROOT_DIR), name="static")


class _UTF8StaticFiles(StaticFiles):
    """txt 响应补 charset=utf-8，否则浏览器按本地编码猜，中文日志会乱码"""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        if response.headers.get("content-type", "").startswith("text/plain"):
            response.headers["content-type"] = "text/plain; charset=utf-8"
        return response


# 日志文件服务：浏览器直接访问 /logs/app.txt、/logs/app-2026-07-07.txt 查看日志
os.makedirs(settings.LOG_DIR, exist_ok=True)
app.mount("/logs", _UTF8StaticFiles(directory=settings.LOG_DIR), name="logs")


@app.get("/health", tags=["健康检查"])
def health():
    return {
        "status": "ok",
        "mode":   "mock" if settings.USE_MOCK else "production",
    }
