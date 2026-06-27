"""
lib-resource-service 入口
启动后访问 http://localhost:8009/docs 查看自动生成的 API 文档
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.logger import setup_logging

# 导入所有 ORM 模型，确保 create_all 能扫描到表定义
from app.models import resource  # noqa: F401

from app.routers import resources, component, template, icon, image
from app.routers import init_router, vector_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时：初始化日志 + 自动建表 + 创建文件存储子目录"""
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    Base.metadata.create_all(bind=engine)
    for sub in ["component", "template", "icon", "illus", "image"]:
        os.makedirs(os.path.join(settings.FILE_ROOT_DIR, sub), exist_ok=True)
    yield
    # 关闭时无需额外清理


app = FastAPI(
    title="资源库管理服务",
    description="统一管理五类设计资源：组件集、模版、SVG、插画、图片",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(component.router)
app.include_router(template.router)
app.include_router(icon.router)
app.include_router(image.router)
app.include_router(init_router.router)
app.include_router(vector_router.router)

# 静态文件服务：前端可通过 /static/{file_path} 直接访问上传文件
if os.path.exists(settings.FILE_ROOT_DIR):
    app.mount("/static", StaticFiles(directory=settings.FILE_ROOT_DIR), name="static")


@app.get("/health", tags=["健康检查"])
def health():
    return {
        "status": "ok",
        "mode":   "mock" if settings.USE_MOCK else "production",
    }
