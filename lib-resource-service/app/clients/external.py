"""
外部 API 客户端
======================================================
所有对外 HTTP 调用集中在此模块，方便统一管理和替换。

Mock 模式（USE_MOCK=true）：返回模拟数据，不发出任何真实请求。
真实模式（USE_MOCK=false）：使用 httpx 调用配置文件中的 API 地址。

切换为真实调用时，只需将 .env 中 USE_MOCK 改为 false 并填写各 API 地址，
无需改动上层 service 代码。
"""

import httpx
from app.config import settings

# ──────────────────────────────────────────────────────────────────
# Mock 数据定义（USE_MOCK=true 时返回）
# 替换为真实数据时删除或注释此区块即可
# ──────────────────────────────────────────────────────────────────

_MOCK_VERSION = {
    "list": [
        {"id": "mock-version-001", "name": "v1.0.0", "createdAt": "2024-01-01"}
    ]
}

_MOCK_ICONS = [
    {"id": 1,   "name": "下载",  "description": "向下箭头带横线，用于文件下载场景",   "englishName": "download"},
    {"id": 2,   "name": "上传",  "description": "向上箭头，用于文件上传场景",         "englishName": "upload"},
    {"id": 3,   "name": "搜索",  "description": "放大镜图标，用于搜索功能",           "englishName": "search"},
    {"id": 4,   "name": "删除",  "description": "垃圾桶图标，用于删除操作",           "englishName": "delete"},
    {"id": 5,   "name": "编辑",  "description": "铅笔图标，用于编辑操作",             "englishName": "edit"},
]

# ──────────────────────────────────────────────────────────────────
# 组件集相关
# ──────────────────────────────────────────────────────────────────

async def get_component_version(file_key: str) -> dict:
    """
    获取组件库最新版本信息。
    返回格式：{ "list": [{ "id": "版本ID", ... }] }
    调用方取 list[0].id 作为版本 ID。
    """
    if settings.USE_MOCK:
        return _MOCK_VERSION

    url = f"{settings.GET_VERSION_API_URL}/{file_key}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def download_pix_file(file_key: str, version_id: str) -> bytes:
    """
    根据 fileKey 和版本 ID 下载 pix 文件，返回原始字节。
    """
    if settings.USE_MOCK:
        return b"MOCK_PIX_CONTENT"

    url = f"{settings.GET_FILE_API_URL}/{file_key}&{version_id}"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def call_split_api(pix_file_path: str) -> dict:
    """
    调用拆解 API，将 pix 文件拆解为组件 hex + component_index.json。
    参数：pix 文件的绝对路径。
    返回：{ "success": true }
    """
    if settings.USE_MOCK:
        return {"success": True}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(settings.SPLIT_API_URL, json={"file_path": pix_file_path})
        resp.raise_for_status()
        return resp.json()


# ──────────────────────────────────────────────────────────────────
# SVG / 插画相关
# ──────────────────────────────────────────────────────────────────

async def fetch_icon_list() -> list:
    """
    从图标服务拉取数据列表。
    返回格式：[{ "id": 1, "name": "下载", "description": "...", "englishName": "download" }]
    """
    if settings.USE_MOCK:
        return _MOCK_ICONS

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(settings.ICON_API_URL)
        resp.raise_for_status()
        return resp.json()


# ──────────────────────────────────────────────────────────────────
# 图片语义理解
# ──────────────────────────────────────────────────────────────────

def understand_image(image_path: str) -> str:
    """
    调用图片语义理解模块，生成图片的中文语义描述。
    参数：图片文件的绝对路径。
    真实实现是同步 py 模块（app/clients/image_understanding.py），单张耗时约 10~30 秒，
    调用方需以同步路由（def）承载，交由 FastAPI 线程池执行。
    """
    if settings.USE_MOCK:
        import time
        time.sleep(2)
        return "[Mock] 这是一张示例图片的语义描述：画面主体清晰，构图居中，色彩以蓝白为主，适合用于界面展示场景。"

    from app.clients.image_understanding import understand_image as _understand
    return _understand(image_path)


