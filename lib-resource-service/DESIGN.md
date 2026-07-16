# lib-resource-service 设计文档

## 一、项目概述

资源库管理服务，统一管理六类设计资源：组件集、模版、SVG、插画、图片、文件。

提供：
- 资源的存储与检索（MySQL）
- 统一文件上传接收
- 向量智能检索
- 来源管理与分组管理
- 对外提供 REST API，供前端及其他服务调用

---

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 见下方版本说明 |
| Web 框架 | FastAPI | 异步、自动生成 OpenAPI 文档 |
| ASGI 服务器 | Uvicorn | 生产环境可配合 Gunicorn |
| 数据库驱动 | SQLAlchemy 2.x | 同步模式，支持连接池 |
| 数据校验 | Pydantic v2 | FastAPI 内置，请求/响应模型 |
| 文件上传 | python-multipart | FastAPI 文件上传依赖 |
| HTTP 客户端 | httpx | 调用外部 API |
| 配置管理 | python-dotenv | 读取 .env 文件 |

---

## 三、数据库设计

### 3.1 表结构总览

数据库包含 **4 张表**：

```
resources (主表)
    │
    ├─ N:1 ── resource_sources   source_id → resource_sources.id
    ├─ N:1 ── resource_groups    group_id → resource_groups.id
    └─ 1:N ── resource_tags      resource_id → resources.id
```

| 表名 | 说明 |
|------|------|
| `resources` | 资源主表（通用字段） |
| `resource_tags` | 标签表（一对多） |
| `resource_sources` | 来源表（数据来源管理） |
| `resource_groups` | 分组表（树形分类结构） |

**详细表结构请查看：[DATABASE.md](./DATABASE.md)**

### 3.2 资源类型映射

| resource_type值 | 类型名称 | 英文名 |
|----------------|---------|--------|
| 1 | 组件集 | component |
| 2 | 模版 | template |
| 3 | SVG图标 | icon |
| 4 | 插画 | illus |
| 5 | 图片 | image |
| 6 | 文件 | file |

### 3.3 表设计要点

- **主表统一**：通用字段都在 `resources` 表，使用 `resource_type` 区分类型
- **来源必填**：每个资源必须关联一个来源（`source_id`）
- **分组按来源独立**：分组树按来源独立，不同来源有不同的分组结构
- **软删除**：`is_deleted` 字段标记删除状态，数据不物理删除
- **向量文本**：`vector_text` 字段由四个字段拼接：name + description + tags + search_text

---

## 四、后端模块设计

### 目录结构

```
lib-resource-service/
├── app/
│   ├── main.py               # FastAPI 实例、路由注册
│   ├── config.py             # 所有配置项从 .env 读取
│   ├── database.py           # SQLAlchemy engine + session
│   ├── enums.py              # ResourceType IntEnum 定义
│   ├── models/
│   │   └── resource.py       # ORM 模型：Resource, ResourceTag, ResourceSource, ResourceGroup
│   ├── schemas/
│   │   ├── resource.py       # 通用资源请求/响应
│   │   ├── source.py         # 来源管理请求/响应
│   │   ├── group.py          # 分组管理请求/响应
│   │   └── upload.py         # 批量上传响应
│   ├── routers/
│   │   ├── resources.py      # 资源 CRUD + 向量同步
│   │   ├── upload.py         # 统一批量上传
│   │   ├── sources.py        # 来源管理 CRUD
│   │   ├── group.py          # 分组管理 CRUD
│   │   ├── search.py         # 向量搜索
│   │   ├── vector_router.py  # 向量服务代理
│   │   └── init_router.py    # 初始化入库
│   ├── services/
│   │   ├── resource_service.py   # 通用 DB CRUD 封装
│   │   ├── upload_service.py     # 统一批量上传逻辑
│   │   ├── source_service.py     # 来源管理 CRUD
│   │   ├── group_service.py      # 分组管理 CRUD
│   │   ├── vector_sync_service.py # 向量同步逻辑
│   │   ├── vector_text_builder.py # 向量文本构建与入库
│   │   └── init_service.py       # 初始化入库逻辑
│   └── clients/
│       ├── external.py           # 外部 API 调用（含 Mock）
│       └── vector_client.py      # 向量服务客户端
├── storage/                      # 文件存储根目录
├── requirements.txt
├── .env.example
└── DESIGN.md
```

### 模块职责说明

| 模块 | 职责 |
|------|------|
| `routers/` | 接收 HTTP 请求，参数校验，调用 service，返回响应 |
| `services/` | 业务逻辑：文件操作、DB 写入、向量同步等 |
| `clients/` | 封装外部 HTTP 调用（向量服务、图片理解等） |
| `models/` | SQLAlchemy ORM 表定义 |
| `schemas/` | Pydantic 请求/响应模型，负责类型转换 |

---

## 五、对外 API 设计

### 资源管理

```
GET  /api/resources
     ?type=component|template|icon|illus|image|file
     &source_id=1
     &group_id=1
     &search=关键词
     &page=1
     &limit=20

GET  /api/resources/{id}
PUT  /api/resources/{id}    更新元数据（名称、描述、标签等）
DELETE /api/resources/{id}  软删除
DELETE /api/resources/batch?type=&source_id=&group_id=  批量删除
POST /api/resources/{id}/understand  语义理解
POST /api/resources/sync-vectors?type=  向量同步
```

### 统一上传

```
POST /api/upload?type=icon|illus|template|image|file
Content-Type: multipart/form-data

参数：
- files: 资源文件列表
- thumbnails: 缩略图列表（PNG 格式）
- items: JSON 字符串，包含元数据数组
- source_id: 来源ID（必填）

items 格式：
[
  {
    "name": "资源名称",
    "description": "描述",
    "group_id": 1,
    "width": 100,
    "height": 100,
    "file_url": "https://...",  // 可选
    "tags": ["标签1", "标签2"],
    "search_text": "关键词",
    "raw_data": {}  // 原始数据
  }
]
```

### 来源管理

```
GET    /api/sources
POST   /api/sources
PUT    /api/sources/{id}
DELETE /api/sources/{id}
```

### 分组管理

```
GET    /api/groups?type={type}&source_id={id}  分组树
POST   /api/groups
PUT    /api/groups/{id}
DELETE /api/groups/{id}
PUT    /api/groups/{id}/move
```

### 向量搜索

```
POST /api/vector/search

请求体：
{
  "type": "component",
  "queries": ["蓝色按钮"],
  "mode": "hybrid",  // vector | text | hybrid
  "top_k": 10,
  "filters": {}
}

响应：
{
  "results": [
    [{ "id": 1, "name": "主按钮", "score": 0.92, ... }]
  ]
}
```

### 初始化

```
POST /api/init
POST /api/init/component
POST /api/init/icon
POST /api/init/template
```

### 静态文件

```
GET /static/{file_path}
GET /health
GET /docs
```

---

## 六、前端页面设计

### 统一管理页面

所有资源类型共用一套管理页面：

| 区域 | 内容 |
|------|------|
| 左侧栏 | 来源选择 + 分组树（按来源加载） |
| 工具栏 | ZIP上传、批量上传、向量同步、清空数据 |
| 搜索框 | 关键词搜索 |
| 表格 | 资源列表，支持分页 |
| 详情侧边栏 | 左右布局：左侧预览图+语义生成，右侧基础信息+向量库映射 |

### 统一上传页面

| 区域 | 内容 |
|------|------|
| ZIP 选择 | 选择包含 config.json 的 ZIP 包 |
| 预览表格 | 显示解析后的数据，支持编辑 |
| 提交按钮 | 批量提交到后端 |

---

## 七、配置项（.env）

```env
# 服务
PORT=8009

# 数据库（二选一）
DB_URL=sqlite:///./dev.db
# 或
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=resource_lib
DB_USER=root
DB_PASSWORD=

# 文件存储
FILE_ROOT_DIR=./storage

# 外部服务
USE_MOCK=true
VECTOR_SERVICE_URL=http://localhost:8008
```

---

## 八、核心逻辑

### 向量文本构建

```python
def build_vector_text(resource) -> str:
    parts = [resource.name or ""]
    if resource.description:
        parts.append(resource.description)
    if resource.tags:
        parts.append(" ".join([t.tag for t in resource.tags]))
    if resource.search_text:
        parts.append(resource.search_text)
    return " ".join(parts)
```

### 来源管理

每个资源必须关联一个来源。默认来源：

- `manual_component` - 手动上传-组件
- `manual_template` - 手动上传-模版
- `manual_icon` - 手动上传-SVG
- `manual_illus` - 手动上传-插画
- `manual_image` - 手动上传-图片
- `manual_file` - 手动上传-文件

### 分组管理

分组按来源独立：
- 同一资源类型 + 同一来源有独立的分组树
- 不同来源的分组互不影响

---

## 九、相关文档

- [DATABASE.md](./DATABASE.md) - 数据库表结构详细说明
- [CLAUDE.md](../CLAUDE.md) - 项目导引和开发指南