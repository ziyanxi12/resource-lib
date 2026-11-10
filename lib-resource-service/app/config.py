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
    # 对外访问的完整域名（不含路径前缀），用于生成静态文件完整 URL
    # 留空时自动从请求头推断；生产环境建议显式配置
    # 示例：PUBLIC_ORIGIN=http://resource-lib.local
    PUBLIC_ORIGIN: str = os.getenv("PUBLIC_ORIGIN", "")

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

    # ── 访问日志（requests.txt，全量请求一行一条）──────────────
    ACCESS_LOG_ENABLED: bool = True
    SLOW_REQUEST_MS: int = 200
    REQUEST_LOG_RETENTION_DAYS: int = 30

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

    # ── 搜索日志 ──────────────────────────────────────────────
    # true = 采集 POST /api/vector/search 请求日志到 vector_search_logs 表
    SEARCH_LOG_ENABLED: bool = os.getenv("SEARCH_LOG_ENABLED", "true").lower() == "true"

    # ── 搜索应用导入 ──────────────────────────────────────────
    # true = 启动时从 SEARCH_APPS_IMPORT_FILE 导入搜索应用（用于测试→生产迁移，首次导入后改回 false）
    SEARCH_APPS_AUTO_IMPORT: bool = os.getenv("SEARCH_APPS_AUTO_IMPORT", "false").lower() == "true"
    SEARCH_APPS_IMPORT_FILE: str = os.getenv("SEARCH_APPS_IMPORT_FILE", "./storage/search_apps.json")

    # ── 访问白名单 ────────────────────────────────────────────
    # true = 启用白名单校验（/api/whitelist/check 生效），false = 开发环境放行所有账号
    WHITELIST_ENABLED: bool = os.getenv("WHITELIST_ENABLED", "false").lower() == "true"

    # ── 设计系统模块白名单（与上方完全隔离）─────────────────────
    # 只作用于 /api/design-systems/whitelist/check，不影响原白名单；
    # 默认 true = 设计系统管理台白名单始终生效（放行请往 ds_whitelist_accounts 加账号）
    DS_WHITELIST_ENABLED: bool = os.getenv("DS_WHITELIST_ENABLED", "true").lower() == "true"

    # ── 设计系统管理台登录过期 ────────────────────────────────
    # X-User-Data 载荷内 loginTime 距今超过该小时数 → 管理台端点 401（前端清登录态跳登录页）；
    # 0 = 关闭校验（本地调试 / 存量测试）；展示端公开端点（GET 列表、POST views）不受影响
    DS_LOGIN_TTL_HOURS: int = int(os.getenv("DS_LOGIN_TTL_HOURS", "24"))

    # ── 用户认证加密 ──────────────────────────────────────────
    # AES-256-CBC 密钥（32字节 base64），前后端必须一致
    AUTH_AES_KEY: str = os.getenv("AUTH_AES_KEY", "")

    # ── Mock 开关 ─────────────────────────────────────────────
    # true = 不调用真实外部 API，全部返回模拟数据，便于本地开发
    USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

    # ── 外部 API 地址（USE_MOCK=false 时生效）────────────────
    GET_VERSION_API_URL:       str = os.getenv("GET_VERSION_API_URL", "")
    GET_FILE_API_URL:          str = os.getenv("GET_FILE_API_URL", "")
    SPLIT_API_URL:             str = os.getenv("SPLIT_API_URL", "")
    ICON_API_URL:              str = os.getenv("ICON_API_URL", "")

    # 用户信息查询 API：GET {USER_INFO_API_URL}?account=xxx（服务端直连，无 cookie/token 依赖）。
    # 两个消费方：resolve_display_names（显示名兜底）+ 设计系统打点身份完整化（users 表未命中时按
    # account 精确补全 nickName/dept 并回写缓存）；留空 = 兜底链直接降级（不外部查询）
    USER_INFO_API_URL:         str = os.getenv("USER_INFO_API_URL", "")

    # 用户搜索 API（人员管理联想搜索），需转发 cookie 和 uiplustoken
    USER_SEARCH_API_URL:       str = os.getenv("USER_SEARCH_API_URL", "")

    # ── 上传限制 ───────────────────────────────────────────────
    # 默认值可通过环境变量配置，但有硬编码最大上限
    MAX_UPLOAD_COUNT: int = int(os.getenv("MAX_UPLOAD_COUNT", "50000"))
    MAX_ZIP_SIZE_MB: int = int(os.getenv("MAX_ZIP_SIZE_MB", "2000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "500"))

    # 硬编码最大上限（不可配置，保护系统）
    MAX_UPLOAD_COUNT_LIMIT: int = 50000
    MAX_ZIP_SIZE_MB_LIMIT: int = 2000
    MAX_FILE_SIZE_MB_LIMIT: int = 500

    def get_effective_upload_limit(self) -> tuple[int, int, int]:
        """返回生效的上传限制（取配置值与硬上限的较小值）"""
        return (
            min(self.MAX_UPLOAD_COUNT, self.MAX_UPLOAD_COUNT_LIMIT),
            min(self.MAX_ZIP_SIZE_MB, self.MAX_ZIP_SIZE_MB_LIMIT),
            min(self.MAX_FILE_SIZE_MB, self.MAX_FILE_SIZE_MB_LIMIT),
        )


# 全局单例，其他模块 from app.config import settings 即可使用
settings = Settings()
