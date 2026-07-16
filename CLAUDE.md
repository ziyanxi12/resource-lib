# CLAUDE.md — 项目导引

## 项目概览

设计资源库管理系统，管理六类资源：**组件集 / 模版 / SVG / 插画 / 图片 / 文件**。

- 后端：`lib-resource-service/`（Python FastAPI + SQLAlchemy + MySQL）
- 前端：`lib-resource-ui/`（React 18 + Ant Design 5 + Vite）
- 存储：`lib-resource-service/storage/`（本地文件，结构见下）

---

## 后端结构

```
lib-resource-service/
├── app/
│   ├── main.py              # FastAPI 入口，注册路由、CORS、静态文件
│   ├── config.py            # 全局配置，从 .env 读取
│   ├── database.py          # SQLAlchemy engine / session / Base
│   ├── enums.py             # ResourceType 枚举（1~6 对应六类资源）
│   ├── models/
│   │   └── resource.py      # ORM：Resource / ResourceTag / ResourceSource / ResourceGroup
│   ├── schemas/
│   │   ├── resource.py      # ResourceOut / ResourceUpdateRequest
│   │   ├── source.py        # SourceOut / SourceCreate / SourceUpdate
│   │   ├── group.py         # GroupOut / GroupCreate
│   │   └── upload.py        # BatchUploadResponse
│   ├── routers/
│   │   ├── resources.py     # 通用 CRUD + /categories + /sync-vectors
│   │   ├── upload.py        # 统一批量上传接口
│   │   ├── sources.py       # 来源管理 CRUD
│   │   ├── group.py         # 分组管理 CRUD
│   │   ├── search.py        # 向量搜索
│   │   ├── vector_router.py # 向量服务代理
│   │   └── init_router.py   # /api/init/*（批量初始化入库）
│   ├── services/
│   │   ├── resource_service.py   # 通用 CRUD（所有 service 都调这里）
│   │   ├── upload_service.py     # 统一批量上传逻辑
│   │   ├── source_service.py     # 来源管理 CRUD
│   │   ├── group_service.py      # 分组管理 CRUD
│   │   ├── vector_sync_service.py # 向量同步逻辑
│   │   ├── vector_text_builder.py # 向量文本构建
│   │   └── init_service.py       # 从 storage/ 读预置文件批量入库
│   └── clients/
│       ├── external.py      # 外部 API 调用（含 Mock 实现）
│       └── vector_client.py # 向量服务客户端
├── storage/                  # 文件存储根目录（FILE_ROOT_DIR）
│   ├── component/           # 组件集文件
│   ├── icon/                # SVG 文件
│   ├── illus/               # 插画文件
│   ├── template/            # 模版文件
│   ├── image/               # 图片文件（含缩略图）
│   └── file/                # 通用文件
├── requirements.txt
├── .env                      # 实际配置（不入 git）
└── .env.example              # 配置模板
```

---

## 数据库

启动时 `create_all` 自动建表，**无需手动建表或迁移**。

### 表结构总览

```
resources (主表)
    │
    ├─ N:1 ── resource_sources   source_id → resource_sources.id
    ├─ N:1 ── resource_groups    group_id → resource_groups.id
    └─ 1:N ── resource_tags      resource_id → resources.id
```

**详细表结构见：DATABASE.md**

### resources 主表关键字段

| 字段 | 说明 |
|------|------|
| `resource_type` | 1=组件集 2=模版 3=SVG 4=插画 5=图片 6=文件 |
| `source_id` | 来源ID（必填），关联 resource_sources 表 |
| `name` | 资源名称 |
| `file_name` | 文件名，如 `abc.svg` |
| `file_path` | 相对于 FILE_ROOT_DIR 的路径 |
| `file_url` | 外部文件链接 |
| `thumbnail_path` | 缩略图路径（统一存储在 image/ 目录） |
| `search_text` | 业务搜索关键词 |
| `vector_text` | 向量文本（name + description + tags + search_text 拼接） |
| `raw_data` | 原始数据 JSON |
| `group_id` | 所属分组ID |

---

## 核心逻辑约定

### 统一上传接口

所有资源类型使用统一的上传接口：

```
POST /api/upload?type={icon|illus|template|image|file}
```

**请求参数**（multipart/form-data）：
- `files` - 资源文件列表
- `thumbnails` - 缩略图列表（PNG 格式）
- `items` - JSON 字符串，包含元数据数组
- `source_id` - 来源ID（必填）

### 向量文本构建

```python
vector_text = name + description + tags + search_text
```

### 来源管理

每个资源必须关联一个来源（`source_id` 必填）。来源类型：
- 手动上传（manual_*）
- API 同步（api_*）
- Figma 同步（figma_*）

### 分组管理

分组按来源独立，每种资源类型 + 来源有独立的分组树。

---

## 前端结构

```
lib-resource-ui/src/
├── App.tsx          # 布局 + 左侧导航，页面切换
├── api.ts           # API 调用封装
└── pages/
    ├── ResourceOverview.tsx    # 数据总览
    ├── ResourceManage.tsx      # 统一管理页面（所有类型共用）
    ├── ResourceUpload.tsx      # 统一上传页面（支持 ZIP 上传）
    └── components/
        ├── ResourceTable.tsx   # 统一表格组件
        ├── GroupTree.tsx       # 分组树组件
        └── DetailDrawer.tsx    # 详情侧边栏
```

前端开发服务器（port 5173）已配置代理：`/api` 和 `/static` → `http://localhost:8009`。

---

## 常见改动指引

| 改动 | 要动哪些文件 |
|------|-------------|
| 加新资源类型 | `enums.py` 加枚举 → 前端 `ResourceManage.tsx` 加路由 |
| 加/改 API 字段 | `models/resource.py`（ORM） → `schemas/resource.py`（Pydantic） → `routers/resources.py` 的 `_fmt()` |
| 修改上传逻辑 | `services/upload_service.py` |
| 修改初始化逻辑 | `services/init_service.py` |
| 修改向量同步 | `services/vector_sync_service.py` / `vector_text_builder.py` |
| 加前端页面 | `pages/` 下新建 → `App.tsx` 注册导航和路由 |

---

## 环境配置速查

```env
DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD  # MySQL（留空 DB_URL 时生效）
DB_URL=sqlite:///./dev.db                             # 本地 SQLite 快速启动
FILE_ROOT_DIR=./storage                               # 文件存储根目录
USE_MOCK=true                                         # 本地开发不调外部 API
VECTOR_SERVICE_URL=http://localhost:8008              # 向量服务地址
```

启动命令：
```bash
# 后端
cd lib-resource-service && uvicorn app.main:app --reload --port 8009

# 前端
cd lib-resource-ui && npm run dev
```

---

## 主要 API

```
# 资源管理
GET    /api/resources              列表（?type=&source_id=&group_id=&search=&page=&limit=）
GET    /api/resources/{id}         详情
PUT    /api/resources/{id}         更新元数据
DELETE /api/resources/{id}         软删除
DELETE /api/resources/batch        批量删除（?type=&source_id=&group_id=）
POST   /api/resources/{id}/understand  语义理解
POST   /api/resources/sync-vectors     向量同步

# 统一上传
POST   /api/upload?type={icon|illus|template|image|file}  批量上传

# 来源管理
GET    /api/sources                来源列表
POST   /api/sources                创建来源
PUT    /api/sources/{id}           更新来源
DELETE /api/sources/{id}           删除来源

# 分组管理
GET    /api/groups?type={type}&source_id={id}  分组树
POST   /api/groups                 创建分组
PUT    /api/groups/{id}            更新分组
DELETE /api/groups/{id}            删除分组
PUT    /api/groups/{id}/move       移动分组

# 向量搜索
POST   /api/vector/search          向量搜索

# 初始化
POST   /api/init                   初始化全部
POST   /api/init/component         初始化组件
POST   /api/init/icon              初始化图标+插画
POST   /api/init/template          初始化模版

# 静态文件
GET    /static/{file_path}         访问上传文件
```