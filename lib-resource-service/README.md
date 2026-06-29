# lib-resource-service

资源库管理服务（Python / FastAPI），统一管理五类设计资源：组件集、模版、SVG、插画、图片。

---

## 目录结构

```
lib-resource-service/
├── app/
│   ├── main.py               # 入口：注册路由、启动建表、静态文件服务
│   ├── config.py             # 所有配置项（从 .env 读取）
│   ├── database.py           # 数据库连接（SQLite / MySQL 二选一）
│   ├── enums.py              # ResourceType 枚举，DB 整数 ↔ API 字符串
│   ├── models/resource.py    # ORM 表定义（resources / resource_tags / component_variants / resource_icons）
│   ├── schemas/              # Pydantic 请求/响应模型（每类资源一个文件）
│   ├── clients/
│   │   └── external.py       # ★ 所有外部 API 调用集中在此，Mock 开关在这里
│   ├── services/             # 业务逻辑（每类资源一个文件）
│   │   ├── resource_service.py   # 通用 CRUD
│   │   ├── component_service.py  # 组件集同步流程
│   │   ├── template_service.py   # 模版写文件 + 写 DB
│   │   ├── icon_service.py       # SVG/插画同步
│   │   └── image_service.py      # 图片上传
│   └── routers/              # HTTP 路由（每类资源一个文件）
├── component_map.json         # 组件库 fileKey → 名称 映射表
├── requirements.txt
├── .env.example
└── DESIGN.md                  # 完整设计文档
```

---

## 初始化

### 1. Python 环境

```bash
# 推荐 Python 3.11+
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置文件

```bash
cp .env.example .env
```

编辑 `.env`，按需填写：

```env
PORT=8009

# 本地开发用 SQLite（无需安装 MySQL）
DB_URL=sqlite:///./dev.db

# 生产环境用 MySQL（注释掉 DB_URL，填写下方字段）
# DB_URL=
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_NAME=resource_lib
# DB_USER=root
# DB_PASSWORD=yourpassword

FILE_ROOT_DIR=./storage          # 上传文件存储根目录
COMPONENT_MAP_FILE=./component_map.json

USE_MOCK=true                    # true=不调用真实外部 API
```

> **数据库会自动建表**，启动时 `Base.metadata.create_all()` 自动执行，无需手动建表。  
> MySQL 需提前创建数据库：`CREATE DATABASE resource_lib CHARACTER SET utf8mb4;`

### 3. 启动服务

```bash
# 开发模式（热重载）
.venv/bin/uvicorn app.main:app --reload --port 8009

# 生产模式
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8009 --workers 2
```

启动后：
- API 文档：http://localhost:8009/docs
- 健康检查：http://localhost:8009/health

---

## 对接真实 API 时改哪里

所有外部 API 调用集中在 **`app/clients/external.py`**，每个函数都有 Mock 分支和真实分支。

**步骤一：** `.env` 中填写真实地址并关闭 Mock：

```env
USE_MOCK=false

GET_VERSION_API_URL=http://your-service/api/getVersion
GET_FILE_API_URL=http://your-service/api/getFile
SPLIT_API_URL=http://your-service/split
REBUILD_COMPONENT_API_URL=http://your-service/api/rebuild/component
ICON_API_URL=http://your-service/api/icon
REBUILD_ICON_API_URL=http://your-service/api/rebuild/icon
```

**步骤二：** 只需确认 `external.py` 中各函数的请求/响应格式与真实 API 一致，如有差异在对应函数内调整即可：

| 函数 | 对应 API | 注意点 |
|------|---------|--------|
| `get_component_version(file_key)` | `GET_VERSION_API_URL/{fileKey}` | 返回值需包含 `list[0].id` |
| `download_pix_file(file_key, version_id)` | `GET_FILE_API_URL/{fileKey}&{versionId}` | 返回原始字节 |
| `call_split_api(pix_path)` | `SPLIT_API_URL` | POST，body 包含文件路径 |
| `call_rebuild_component_api()` | `REBUILD_COMPONENT_API_URL` | POST，无需 body |
| `fetch_icon_list()` | `ICON_API_URL` | 返回 `[{id, name, description, englishName}]` |
| `call_rebuild_icon_api()` | `REBUILD_ICON_API_URL` | POST，无需 body |

**步骤三：** 如果 `component_index.json` 的字段名与当前映射不同，在 `app/services/component_service.py` 的 `_write_to_db()` 函数中调整字段映射：

```python
# 当前映射（修改这里）
"name":       comp.get("name"),
"unique_key": comp.get("componentKey"),
"file_path":  comp.get("hexFile"),
"domain":     domain,          # 来自顶层 domain 字段
```

---

## 数据初始化

服务启动后，调用初始化接口将 `storage/` 下的预置文件批量写入数据库。**接口可重复调用（幂等）**，已存在的记录会更新，不会重复插入。

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/init` | 一次性导入全部类型 |
| POST | `/api/init/component` | 仅导入组件集 |
| POST | `/api/init/icon` | 仅导入 SVG + 插画 |
| POST | `/api/init/template` | 仅导入模版 |

### 各类型数据来源与格式

**组件集**

入口文件：`storage/component/component_map.json`
```json
[
  { "indexPath": "component/ICT_UI/component_index.json" }
]
```

按 `indexPath` 找到各组件库的索引文件 `component_index.json`：
```json
{
  "domain": "ICT_UI",
  "componentSets": [
    {
      "name": "文字链接",
      "guid": "8229:277383",
      "componentKey": "be1d...",
      "canvasName": "1.基础类",
      "hexFile": "component/be1d....txt",
      "variants": [
        {
          "name": "size=normal, disabled=false",
          "guid": "8229:277395",
          "variantKey": "f884...",
          "parentKey": "be1d...",
          "componentProps": [{ "name": "text", "type": "TEXT" }]
        }
      ]
    }
  ]
}
```

以 variant 为粒度入库，每条 variant 写：
- `resources`（upsert key：`name + resource_type`）
- `component_variants`（upsert key：`variant_key`）

**SVG / 插画**

- SVG：`storage/icon/icons.json`
- 插画：`storage/illus/illus.json`

```json
[
  { "id": 100, "name": "首页", "englishName": "home", "category": "navigation", "description": "..." }
]
```

每条写 `resources` + `resource_icons`（upsert key：`name + resource_type`）。

**模版**

`storage/template/templates.json`，每次调用均 create 新记录（**不幂等**），只写 `resources`。

---

## 主要 API

```
GET    /api/resources              列表（?type=&search=&page=&limit=）
GET    /api/resources/{id}         详情
PUT    /api/resources/{id}         更新元数据
DELETE /api/resources/{id}         软删除

GET    /api/component/list         组件库列表（读 component_map.json）
POST   /api/component/sync         同步组件集（完整流程）

POST   /api/template/upload        上传模版 hex 数据

POST   /api/icon/sync              同步 SVG 或插画（body: {type: "svg"|"illustration"}）

POST   /api/image/upload           上传图片（multipart/form-data）

POST   /api/vector/search          向量搜索（支持单条/批量，见下方说明）

GET    /static/{file_path}         访问上传文件
GET    /health                     健康检查
GET    /docs                       Swagger API 文档
```

---

## 向量搜索

**POST** `/api/vector/search`

统一接口，`queries` 传一个或多个查询词，`results` 始终为二维数组，顺序与 `queries` 一一对应。

### 请求

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| type | string | 是 | — | `component` / `component_set` / `icon` / `svg` / `illustration` |
| queries | array[string] | 是 | — | 查询文本列表，至少 1 条 |
| mode | string | 否 | `hybrid` | `vector` / `text` / `hybrid` |
| top_k | integer | 否 | `10` | 每个 query 返回条数 |
| filters | object | 否 | — | 精确过滤条件，透传给向量服务 |
| hybrid_weight | float | 否 | `0.7` | hybrid 模式下向量分数权重（0~1） |

```json
{
  "type": "component",
  "queries": ["蓝色按钮", "输入框"],
  "mode": "hybrid",
  "top_k": 5
}
```

### 响应

`results` 为二维数组，每项对应一个 query 的结果，结构与 `/api/resources` 列表项相同，额外附 `score` 字段。

```json
{
  "results": [
    [
      { "id": 1, "name": "主按钮", "score": 0.92, ... }
    ],
    [
      { "id": 5, "name": "文本输入框", "score": 0.88, ... }
    ]
  ]
}
```

> **依赖**：需配置 `.env` 中的 `VECTOR_SERVICE_URL`，指向向量管理服务地址。
