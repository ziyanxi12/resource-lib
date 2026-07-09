import os
from dotenv import load_dotenv

# 优先加载 .env 文件，不覆盖已存在的环境变量
load_dotenv(override=False)


class Settings:
    """
    全局配置，所有配置项从环境变量读取，.env 文件中设置默认值。
    新增配置项时：① 在此添加属性 ② 在 .env.example 补充说明
    """

    # ── 服务 ──────────────────────────────────────────────────
    PORT: int     = int(os.getenv("PORT", "8009"))
    # nginx 路径前缀，留空表示直接暴露（无前缀）
    # 例如 nginx location /resource-lib/ → proxy_pass http://127.0.0.1:8009/
    # 则此处填 ROOT_PATH=/resource-lib
    ROOT_PATH: str = os.getenv("ROOT_PATH", "")

    # ── 数据库 ────────────────────────────────────────────────
    # DB_URL 直接指定完整连接串，优先级高于下方 MySQL 分项配置
    # 本地开发用 SQLite：DB_URL=sqlite:///./dev.db
    # 生产 MySQL：留空，填写下方 DB_HOST 等字段
    DB_URL: str      = os.getenv("DB_URL", "")
    DB_HOST: str     = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int     = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str     = os.getenv("DB_NAME", "resource_lib")
    DB_USER: str     = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # ── 文件存储 ──────────────────────────────────────────────
    # 所有 file_path 均相对于此目录；实际绝对路径 = FILE_ROOT_DIR + file_path
    FILE_ROOT_DIR: str = os.getenv("FILE_ROOT_DIR", "./storage")

    # ── 组件库映射表 ──────────────────────────────────────────
    # JSON 文件，格式：[{ "fileKey": "xxx", "name": "组件库名称" }]
    COMPONENT_MAP_FILE: str = os.getenv("COMPONENT_MAP_FILE", "./storage/component/component_map.json")


    # ── 日志 ──────────────────────────────────────────────────────
    LOG_DIR:   str = os.getenv("LOG_DIR",   "./logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

    # ── 翻译文件 ──────────────────────────────────────────────────
    # 组件属性值中文翻译表，build_component_text 使用
    TRANSLATION_FILE: str = os.getenv(
        "TRANSLATION_FILE",
        "./storage/component/value_translations.json",
    )

    # ── 向量服务 ──────────────────────────────────────────────────
    VECTOR_SERVICE_URL: str     = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8000")
    VECTOR_SERVICE_ENABLED: bool = os.getenv("VECTOR_SERVICE_ENABLED", "false").lower() == "true"
    VECTOR_SEARCH_MODE: str     = os.getenv("VECTOR_SEARCH_MODE", "vector")

    # ── Mock 开关 ─────────────────────────────────────────────
    # true = 不调用真实外部 API，全部返回模拟数据，便于本地开发
    USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

    # ── 外部 API 地址（USE_MOCK=false 时生效）────────────────
    GET_VERSION_API_URL:       str = os.getenv("GET_VERSION_API_URL", "")
    GET_FILE_API_URL:          str = os.getenv("GET_FILE_API_URL", "")
    SPLIT_API_URL:             str = os.getenv("SPLIT_API_URL", "")
    ICON_API_URL:              str = os.getenv("ICON_API_URL", "")


# 全局单例，其他模块 from app.config import settings 即可使用
settings = Settings()
