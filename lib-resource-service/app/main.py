"""
lib-resource-service 入口
启动后访问 http://localhost:8009/docs 查看自动生成的 API 文档
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
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
from app.models import search_log  # noqa: F401
from app.models import search_app  # noqa: F401
from app.models import search_log_filter  # noqa: F401
from app.models import search_log_result  # noqa: F401
from app.models import search_daily_stats  # noqa: F401
from app.models import operation_log  # noqa: F401
from app.models import user  # noqa: F401

from app.routers import resources, upload
from app.routers import vector_router, group
from app.routers import sources, init_router
from app.routers import resource_types
from app.routers import import_task
from app.routers import search_log
from app.routers import search_app
from app.routers import search_stats
from app.routers import ai_enrich
from app.routers import dimensions
from app.routers import operation_log

from app.middleware.search_log_middleware import SearchLogMiddleware
from app.middleware.auth_middleware import AuthMiddleware

# ===== 移除上传限制 =====
# 修改 Starlette 的内存阈值，避免大文件上传时的临时文件问题
# 默认值是 1MB，超过后会写入临时文件，可能导致权限错误
# 设置为 10GB，所有文件都在内存中处理，避免临时文件问题
from starlette.formparsers import MultiPartParser
MultiPartParser.max_file_size = 10 * 1024 * 1024 * 1024  # 10GB


logger = logging.getLogger(__name__)


def _ensure_column(engine, table: str, column: str, ddl: str):
    """检查表是否已有某列，没有则 ALTER TABLE 补上（兼容 SQLite/MySQL），幂等可重复执行。"""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine)
        if table in insp.get_table_names():
            existing = {c["name"] for c in insp.get_columns(table)}
            if column not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                logger.info("自动迁移：%s 表新增列 %s", table, column)
    except Exception as e:
        logger.warning("自动补列失败 %s.%s: %s", table, column, e)


def _ensure_index(engine, table: str, index_name: str, columns: str):
    """检查索引是否存在，不存在则创建（兼容 SQLite/MySQL），幂等可重复执行。"""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine)
        if table in insp.get_table_names():
            existing = {i["name"] for i in insp.get_indexes(table)}
            if index_name not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"CREATE INDEX {index_name} ON {table} ({columns})"))
                logger.info("自动迁移：%s 表新增索引 %s", table, index_name)
    except Exception as e:
        logger.warning("自动补索引失败 %s.%s: %s", table, index_name, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时：初始化日志 + 自动建表 + 创建文件存储子目录"""
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    logger.info("lib-resource-service v%s 启动", __version__)
    Base.metadata.create_all(bind=engine)

    # 增量补列（create_all 只建新表，不修改已有表结构）
    _ensure_column(engine, "vector_search_logs", "business_data", "JSON")
    _ensure_column(engine, "resources", "ai_description", "TEXT")
    _ensure_column(engine, "resources", "updated_by", "VARCHAR(100)")
    _ensure_column(engine, "resource_sources", "created_by", "VARCHAR(100)")
    _ensure_column(engine, "resource_sources", "updated_by", "VARCHAR(100)")

    # 增量补索引（create_all 只建新表的索引，不补已有表）
    _ensure_index(engine, "resources", "idx_resources_type_source_deleted", "resource_type, source_id, is_deleted")
    _ensure_index(engine, "resources", "idx_resources_group", "group_id")
    _ensure_index(engine, "resources", "idx_resources_created_at", "created_at")
    
    # 创建文件存储子目录
    for sub in ["component", "template", "icon", "illus", "image", "file"]:
        os.makedirs(os.path.join(settings.FILE_ROOT_DIR, sub), exist_ok=True)

    # 启动时按需导入搜索应用（测试→生产迁移，SEARCH_APPS_AUTO_IMPORT=true 时生效）
    if getattr(settings, "SEARCH_APPS_AUTO_IMPORT", False):
        from app.database import SessionLocal
        from app.services.search_app_service import import_apps_from_file
        import_db = SessionLocal()
        try:
            result = import_apps_from_file(import_db)
            logger.info("搜索应用导入完成: %s", result)
        except Exception as e:
            logger.warning("搜索应用导入失败: %s", e)
        finally:
            import_db.close()

    # 定时聚合搜索统计（每天凌晨 2:00 聚合前一天数据）
    scheduler = None
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.database import SessionLocal as _SessionLocal
        from app.services import search_stats_service

        def _refresh_yesterday():
            db = _SessionLocal()
            try:
                yesterday = (datetime.now() - timedelta(days=1)).date()
                logger.info("定时任务开始聚合: date=%s", yesterday)
                search_stats_service.refresh_daily_stats(db, yesterday)
            except Exception as e:
                logger.warning("定时聚合搜索统计失败: %s", e)
            finally:
                db.close()

        scheduler = BackgroundScheduler()
        scheduler.add_job(_refresh_yesterday, "cron", hour=2, minute=0, id="refresh_search_stats")
        scheduler.start()
        logger.info("APScheduler 已启动，每天 02:00 聚合搜索统计")
    except ImportError:
        logger.warning("apscheduler 未安装，跳过定时聚合任务（pip install apscheduler 后启用）")

    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="资源库管理服务",
    description="统一管理五类设计资源：组件集、图标、插画、图片、文件",
    version=__version__,
    lifespan=lifespan,
    docs_url=None if settings.ROOT_PATH else "/docs",
    redoc_url=None if settings.ROOT_PATH else "/redoc",
    openapi_url=None if settings.ROOT_PATH else "/openapi.json",
)

# 允许前端跨域访问（开发时前端跑在不同端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SearchLogMiddleware)
app.add_middleware(AuthMiddleware)

# 注册各业务路由
app.include_router(resources.router)
app.include_router(upload.router)
app.include_router(vector_router.router)
app.include_router(group.router)
app.include_router(sources.router)
app.include_router(init_router.router)
app.include_router(resource_types.router)
app.include_router(import_task.router)
app.include_router(search_log.router)
app.include_router(search_app.router)
app.include_router(search_stats.router)
app.include_router(ai_enrich.router)
app.include_router(dimensions.router)
app.include_router(operation_log.router)

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


# ── 自定义文档路由（ROOT_PATH 非空时，引用带前缀的 openapi.json）────────
if settings.ROOT_PATH:
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{settings.ROOT_PATH}/openapi.json",
            title=f"{app.title} - Swagger UI",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=f"{settings.ROOT_PATH}/openapi.json",
            title=f"{app.title} - ReDoc",
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi():
        from app.main import app as _app
        from fastapi.openapi.utils import get_openapi
        schema = get_openapi(
            title=_app.title,
            version=_app.version,
            description=_app.description,
            routes=_app.routes,
        )
        schema["servers"] = [{"url": settings.ROOT_PATH}]
        return schema
