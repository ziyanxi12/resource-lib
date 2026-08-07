from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 支持两种模式：
#   DB_URL 直接指定完整连接串（如 sqlite:///./dev.db）
#   否则拼接 MySQL 连接串
if settings.DB_URL:
    DATABASE_URL = settings.DB_URL
    # SQLite 不支持 pool_pre_ping，connect_args 需特殊处理
    _is_sqlite = DATABASE_URL.startswith("sqlite")
else:
    DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        "?charset=utf8mb4"
    )
    _is_sqlite = False

_engine_kwargs = {"echo": False}
if _is_sqlite:
    # SQLite 多线程需要 check_same_thread=False
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 3600
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if _is_sqlite:
    # WAL 模式：写操作写入 WAL 文件而非主库，读写可并发，写不阻塞读
    # busy_timeout：遇锁等待而非立即报 "database is locked"
    # synchronous=NORMAL：WAL 下安全且更快
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, conn_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# 所有 ORM 模型继承此 Base
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖注入函数，在每个请求中提供独立的数据库会话。
    用法：db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
