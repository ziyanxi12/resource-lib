# lib-resource-service 设计文档

## 一、项目概述

资源库管理服务，统一管理五类设计资源：组件集、模版、SVG、插画、图片。

提供：
- 资源的存储与检索（MySQL）
- 文件上传接收（模版 / SVG / 插画 / 图片）
- 组件集数据同步（调用 lib-admin-service API）
- 对外提供 REST API，供前端及其他服务调用

---

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 见下方版本说明 |
| Web 框架 | FastAPI | 异步、自动生成 OpenAPI 文档 |
| ASGI 服务器 | Uvicorn | 生产环境可配合 Gunicorn |
| 数据库驱动 | aiomysql | 异步 MySQL 驱动 |
| ORM | SQLAlchemy 2.x (async) | 异步模式，支持连接池 |
| 数据迁移 | Alembic | 管理数据库 schema 变更 |
| 数据校验 | Pydantic v2 | FastAPI 内置，请求/响应模型 |
| 文件上传 | python-multipart | FastAPI 文件上传依赖 |
| HTTP 客户端 | httpx | 调用 lib-admin-service 等外部 API |
| 配置管理 | python-dotenv | 读取 .env 文件 |

### Python 版本说明

**建议使用 Python 3.11+，不推荐 3.8。**

Python 3.8 的已知问题：

1. **已停止安全维护**：3.8 EOL 时间为 2024 年 10 月，不再接收安全补丁
2. **类型注解语法受限**：
   - 不支持 `X | Y` 联合类型，需写 `Union[X, Y]`
   - 不支持 `list[str]`、`dict[str, str]`，需写 `List[str]`、`Dict[str, str]`
3. **库版本兼容风险**：FastAPI 0.100+、SQLAlchemy 2.x 虽声称支持 3.8，但新版本会逐步放弃
4. **性能较差**：3.11 相比 3.8 有 10-60% 的性能提升

如果服务器环境只有 3.8，短期可以运行，需注意：
- 所有类型注解加 `from __future__ import annotations`
- 固定依赖版本，避免自动升级破坏兼容性

---

## 三、数据库设计

### 3.1 表结构总览

数据库包含 **5 张表**：

```
resources (主表)
    │
    ├─ 1:N ── resource_tags        resource_id → resources.id
    ├─ 1:1 ── component_variants   resource_id → resources.id (仅 resource_type=1)
    ├─ 1:1 ── resource_icons       resource_id → resources.id (仅 resource_type=3)
    └─ 1:1 ── resource_illus      resource_id → resources.id (仅 resource_type=4)
```

**详细表结构、字段清单、约束说明** 请查看：**[DATABASE.md](./DATABASE.md)**

### 3.2 资源类型映射

| resource_type值 | 类型名称 | 英文名 | 详情表 |
|----------------|---------|--------|--------|
| 1 | 组件集 | component | component_variants |
| 2 | 模版 | template | - |
| 3 | SVG图标 | icon | resource_icons |
| 4 | 插画 | illus | resource_illus |
| 5 | 图片 | image | - |

### 3.3 表设计要点

- **主表统一**：通用字段都在 `resources` 表，使用 `resource_type` 区分类型
- **详情表分离**：每种类型有独立的详情表存储特有字段，通过 1:1 关系关联
- **软删除**：`is_deleted` 字段标记删除状态，数据不物理删除
- **业务主键**：详情表使用业务主键（variant_key/icon_id/illus_id），而非自增ID
- **级联删除**：外键设置 `ondelete="CASCADE"`，删除主表记录时自动删除关联数据

---

## 四、数据来源与存储流程

### 4.1 组件集

**数据来源：**
- `component_map.json` - 组件库映射表（包含 fileKey, name）
- `component_index.json` - 组件集详情（由 `/split` API 拆解 pix 文件后生成）

**前置条件：** 项目中维护一份 `component_map.json` 映射表：

```json
[
  { "fileKey": "abc123", "name": "AAA组件库", "indexPath": "component/abc123/component_index.json" },
  { "fileKey": "def456", "name": "BBB组件库", "indexPath": "component/def456/component_index.json" }
]
```

**入库时提取：**
- `fileKey` → `component_variants.lib_file_key`
- `name` → `component_variants.lib_name`

**完整流程：**
```
读取 component_map.json → 前端展示可选组件库列表
    ↓ 用户选择某个组件库，点击「更新」
后端调用 GET_VERSION_API（/api/getVersion/{fileKey}）
    → 取响应中 list[0].id 作为版本 ID
    ↓
后端调用 GET_FILE_API（/api/getFile/{fileKey}&{versionId}）
    → 下载 pix 文件，暂存到本地
    ↓
后端调用 SPLIT_API（/split）拆解 pix 文件
    → 生成组件 hex 文件到 FILE_ROOT_DIR/component/{fileKey}/
    → 生成 component_index.json
    ↓
解析 component_index.json → UPSERT 写入 resources 表
    ↓
调用 REBUILD_COMPONENT_API → 组件数据向量化入库
    ↓
返回同步结果（新增数、更新数）
```

**`component_index.json` 字段映射：**

| JSON 字段 | DB 表 | DB 字段 |
|-----------|--------|---------|
| 名称 | resources | name |
| `componentKey` | component_variants | component_key |
| hex 路径 | resources | file_path |
| `canvasName` | component_variants | canvas_name |
| `name`（组件集） | component_variants | component_name |
| - | component_variants | lib_file_key, lib_name（来自 component_map.json） |

**关键变化：**
- 组件库信息（`lib_file_key`, `lib_name`）来自 `component_map.json`，而非 `component_index.json`
- 不再使用 `domain` 字段，改用 `lib_name` 表示组件库来源

---

### 4.2 模版

**数据来源：** 前端页面手动填写并粘贴 hex 数据

**完整流程：**
```
前端填写：名称、描述，粘贴 hex 文本
    ↓
后端生成 UUID
    ↓
将 hex 文本写入 FILE_ROOT_DIR/template/{uuid}.txt
    ↓
写入 resources 表（file_path = template/{uuid}.txt）
    ↓
返回成功
```

---

### 4.3 SVG / 插画

**数据来源：** 调用 `ICON_API` 返回的 JSON 数组

**JSON 格式：**
```json
[
  {
    "id": 333,
    "name": "下载",
    "description": "下载图标，向下箭头带横线，用于文件下载、保存到本地等场景",
    "englishName": "download"
  }
]
```

**完整流程：**
```
前端点击「同步」按钮，选择类型（SVG 或插画）
    ↓
后端调用 ICON_API → 获取 JSON 数组
    ↓
将 JSON 保存到 FILE_ROOT_DIR/icon/{type}.json
    ↓
解析 JSON → UPSERT 写入 resources + resource_icons/resource_illus 表
（id → icon_id/illus_id，name → name，englishName → english_name，
  description → description，file_path 为空）
    ↓
调用 REBUILD_ICON_API → 数据向量化入库
    ↓
返回同步结果（新增数、更新数）
```

---

### 4.4 图片

**数据来源：** 前端页面上传图片文件

**完整流程：**
```
前端填写：名称、描述，选择图片文件上传
    ↓
后端生成 UUID，读取文件扩展名
    ↓
将图片存入 FILE_ROOT_DIR/image/{uuid}.{ext}
    ↓
提取图片尺寸 → 填入 width/height 字段
    ↓
写入 resources 表（file_path = image/{uuid}.{ext}）
    ↓
返回成功
```

---

## 五、前端页面设计

共 5 个页面，以 Tab 或侧边菜单切换。

### 5.1 资源总览页

- 顶部 Tab 切换五大类型
- 每个 Tab 下展示该类型资源卡片列表（名称、缩略图、描述）
- 支持关键词搜索、标签筛选、分页
- 每条资源可操作：编辑元数据、删除

### 5.2 组件集管理页

| 区域 | 内容 |
|------|------|
| 组件库列表 | 读取 `component_map.json`，以卡片或列表展示所有可选组件库（fileKey + 名称）|
| 操作按钮 | 每个组件库旁有「更新」按钮，点击后触发完整同步流程 |
| 状态区 | 实时显示当前步骤进度：获取版本 → 下载文件 → 拆解 → 写入 → 向量化 |
| 结果区 | 完成后展示本次新增数、更新数 |

**操作步骤（后端顺序执行）：**
1. 获取版本：`GET_VERSION_API` → 取 `list[0].id`
2. 下载文件：`GET_FILE_API` → 保存 pix 文件
3. 拆解：`SPLIT_API` → 生成 hex + `component_index.json`
4. 写入资源库：解析 JSON → UPSERT DB
5. 向量化：`REBUILD_COMPONENT_API`

### 5.3 模版管理页

| 区域 | 内容 |
|------|------|
| 表单区 | 模版名称（必填）、模版描述（必填）、hex 数据文本框（粘贴）|
| 操作 | 点击「上传」→ 提交到后端 |
| 列表区 | 已上传模版列表，支持删除 |

### 5.4 SVG / 插画管理页

| 区域 | 内容 |
|------|------|
| 操作区 | 类型选择（SVG / 插画），点击「同步」触发数据拉取和向量化 |
| 状态区 | 显示同步进度和结果（新增数、更新数）|
| 列表区 | 已同步的 SVG/插画列表（名称、英文名、描述）|

### 5.5 图片管理页

| 区域 | 内容 |
|------|------|
| 表单区 | 图片名称（必填）、图片描述（必填）、图片上传控件 |
| 操作 | 点击「上传」→ 提交到后端 |
| 列表区 | 已上传图片列表（缩略图预览、名称），支持删除 |

---

## 六、后端模块设计

### 目录结构

```
lib-resource-service/
├── app/
│   ├── main.py               # FastAPI 实例、路由注册、lifespan
│   ├── config.py             # 所有配置项从 .env 读取
│   ├── database.py           # SQLAlchemy async engine + session
│   ├── enums.py              # ResourceType IntEnum 定义
│   ├── models/
│   │   ├── resource.py       # ORM 模型：Resource, ResourceTag
│   ├── schemas/
│   │   ├── resource.py       # 通用资源请求/响应 Pydantic 模型
│   │   ├── component.py      # 组件集专用模型
│   │   ├── template.py       # 模版专用模型
│   │   ├── icon.py           # SVG/插画专用模型
│   │   └── image.py          # 图片专用模型
│   ├── routers/
│   │   ├── resources.py      # GET /api/resources 列表、详情、编辑、删除
│   │   ├── component.py      # POST /api/component/sync（拆解+写入+向量化）
│   │   ├── template.py       # POST /api/template/upload
│   │   ├── icon.py           # POST /api/icon/sync（拉取+写入+向量化）
│   │   └── image.py          # POST /api/image/upload
│   ├── services/
│   │   ├── resource_service.py   # 通用 DB CRUD 封装
│   │   ├── component_service.py  # 解析 component_index.json，写入 DB
│   │   ├── template_service.py   # 写 hex 文件，写入 DB
│   │   ├── icon_service.py       # 解析 icon JSON，写入 DB
│   │   └── image_service.py      # 保存图片文件，提取尺寸，写入 DB
│   └── clients/
│       └── external.py           # 所有外部 API 调用（httpx），地址从 config 读取
├── alembic/
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
├── .gitignore
└── DESIGN.md
```

### 模块职责说明

| 模块 | 职责 |
|------|------|
| `routers/` | 接收 HTTP 请求，参数校验，调用 service，返回响应 |
| `services/` | 业务逻辑：文件操作、DB 写入、调用外部 API 的编排 |
| `clients/external.py` | 封装所有对外 HTTP 调用，地址从 config 读取 |
| `models/` | SQLAlchemy ORM 表定义 |
| `schemas/` | Pydantic 请求/响应模型，负责类型转换（ResourceType 枚举互转）|

---

## 七、对外 API 设计

### 资源查询（通用）

```
GET  /api/resources
     ?type=component_set|template|svg|illustration|image
     &page=1  &limit=20  &search=关键词
GET  /api/resources/{id}
PUT  /api/resources/{id}    更新元数据（名称、描述、排序、标签）
DELETE /api/resources/{id}  软删除
```

### 组件集

```
GET  /api/component/list
  响应：读取 component_map.json，返回可选组件库列表
  响应体：[{ "fileKey": "abc123", "name": "基础组件库" }, ...]

POST /api/component/sync
  请求体：{ "file_key": "abc123" }
  流程：
    1. 调 GET_VERSION_API(/api/getVersion/{fileKey}) → 取 list[0].id
    2. 调 GET_FILE_API(/api/getFile/{fileKey}&{id}) → 下载 pix 文件
    3. 调 SPLIT_API(/split) → 生成 hex + component_index.json
    4. 解析 component_index.json → UPSERT resources 表
    5. 调 REBUILD_COMPONENT_API → 向量化
  响应：{ "added": 10, "updated": 3 }
```

### 模版

```
POST /api/template/upload
  请求体（JSON）：{ "name": "", "description": "", "hex_data": "..." }
  流程：写 hex 文件 → 写 DB
  响应：{ "id": 1, "file_path": "template/uuid.txt" }
```

### SVG / 插画

```
POST /api/icon/sync
  请求体：{ "type": "svg" | "illustration" }
  流程：调 ICON_API → 保存 JSON 文件 → UPSERT DB → 调 REBUILD_ICON_API
  响应：{ "added": 50, "updated": 5 }
```

### 图片

```
POST /api/image/upload
  Content-Type: multipart/form-data
  字段：file（图片文件）、name、description
  流程：保存图片 → 提取尺寸 → 写 DB
  响应：{ "id": 1, "file_path": "image/uuid.png" }
```

### 静态文件访问

```
GET /static/{file_path}    直接访问 FILE_ROOT_DIR 下的文件
```

---

## 八、配置项（.env）

```env
# 服务
PORT=8009

# MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=resource_lib
DB_USER=
DB_PASSWORD=

# 文件存储根目录（所有 file_path 均相对于此目录）
FILE_ROOT_DIR=/data/resources

# 外部 API（调用其他服务，地址均在此配置）
GET_VERSION_API_URL=http://127.0.0.1:xxxx/api/getVersion
GET_FILE_API_URL=http://127.0.0.1:xxxx/api/getFile
SPLIT_API_URL=http://127.0.0.1:3103/split
REBUILD_COMPONENT_API_URL=http://127.0.0.1:3103/api/rebuild/component
ICON_API_URL=http://127.0.0.1:xxxx/api/icon
REBUILD_ICON_API_URL=http://127.0.0.1:xxxx/api/rebuild/icon

# 组件库映射表路径（fileKey → 文件名）
COMPONENT_MAP_FILE=./component_map.json
```

---

## 九、待确认事项

- [ ] 各外部 API 的实际地址（GET_VERSION、GET_FILE、SPLIT、REBUILD、ICON 等）
- [ ] `GET_FILE_API` 的完整 URL 格式确认（`/api/getFile/{fileKey}&{id}` 还是其他形式）
- [ ] `component_map.json` 由谁维护、放在哪个路径
- [ ] MySQL 连接信息（host / port / db name）
- [ ] `FILE_ROOT_DIR` 实际路径
- [ ] Python 版本（建议 3.11，确认服务器环境）
