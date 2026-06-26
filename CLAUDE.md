# CLAUDE.md — 项目导引

## 项目概览

设计资源库管理系统，管理五类资源：**组件集 / 模版 / SVG / 插画 / 图片**。

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
│   ├── enums.py             # ResourceType 枚举（1~5 对应五类资源）
│   ├── models/
│   │   └── resource.py      # ORM：Resource / ResourceTag / ComponentVariant / ResourceIcon
│   ├── schemas/
│   │   ├── resource.py      # ResourceOut / ResourceUpdateRequest
│   │   ├── component.py     # ComponentSyncRequest/Response
│   │   ├── template.py      # TemplateUploadRequest/Response
│   │   ├── icon.py          # IconSyncRequest/Response
│   │   └── image.py         # ImageUploadResponse
│   ├── routers/
│   │   ├── resources.py     # 通用 CRUD + /categories + /all
│   │   ├── component.py     # /api/component/list, /sync
│   │   ├── template.py      # /api/template/upload
│   │   ├── icon.py          # /api/icon/sync
│   │   ├── image.py         # /api/image/upload
│   │   └── init_router.py   # /api/init/*（批量初始化入库）
│   ├── services/
│   │   ├── resource_service.py   # 通用 CRUD（所有 service 都调这里）
│   │   ├── component_service.py  # 组件集同步逻辑
│   │   ├── icon_service.py       # SVG/插画同步逻辑
│   │   ├── template_service.py   # 模版上传逻辑
│   │   ├── image_service.py      # 图片上传逻辑
│   │   └── init_service.py       # 从 storage/ 读预置文件批量入库
│   └── clients/
│       └── external.py      # 外部 API 调用（含 Mock 实现）
├── storage/                  # 文件存储根目录（FILE_ROOT_DIR）
│   ├── component/
│   │   └── component_map.json  # 组件库映射表（fileKey/name/indexPath/updatedAt）
│   ├── icon/
│   │   └── icons.json        # SVG 图标数据
│   ├── illus/
│   │   └── illus.json        # 插画数据
│   ├── template/
│   │   └── templates.json    # 模版初始化数据
│   └── image/                # 上传的图片文件
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
    ├─ 1:N ── resource_tags        resource_id → resources.id
    ├─ 1:1 ── component_variants   resource_id → resources.id
    └─ 1:1 ── resource_icons       resource_id → resources.id
```

### resources 主表关键字段

| 字段 | 说明 |
|------|------|
| `resource_type` | 1=组件集 2=模版 3=SVG 4=插画 5=图片 |
| `name` | 资源名称（与 resource_type 组合作为 upsert key） |
| `file_name` | 文件名，如 `abc.svg` |
| `file_path` | 相对于 FILE_ROOT_DIR 的路径 |
| `raw_data` | 外部 API 返回的原始 JSON 字符串 |
| `is_deleted` | 软删除，0=正常 1=已删除 |

### component_variants 关键字段（resource_type=1）

| 字段 | 说明 |
|------|------|
| `resource_id` | FK → resources.id |
| `canvas_name` | 画布分组名，如 `1.基础类` |
| `component_name` | 组件集名称 |
| `component_guid` | 组件集 guid |
| `component_key` | 组件集 key（即 variant.parentKey），按此字段分组可得同一组件集的所有变体 |
| `name` | 变体属性字符串，如 `size=normal, disabled=false` |
| `guid` | 变体 guid |
| `variant_key` | 变体 key（upsert key） |
| `component_props` | JSON 数组，如 `[{name, type}, ...]` |

### resource_icons 关键字段（resource_type=3/4）

| 字段 | 说明 |
|------|------|
| `resource_id` | FK → resources.id |
| `english_name` | 英文名，如 `home` |
| `category` | 分类，如 `navigation` / `system` / `feedback` |

---

## 核心逻辑约定

### upsert vs create

- **同步类**（组件、图标、插画）→ 用 `upsert_resource(db, data)`，以 `(name, resource_type)` 做幂等更新
- **上传类**（图片、模版）→ 用 `create_resource(db, data)`，每次上传都是新记录

### 初始化入库（`/api/init`）

从 `storage/` 读预置 JSON 文件写入数据库，**不调用外部 API**，**可重复调用（幂等）**。

#### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/init` | 一次性导入全部类型 |
| POST | `/api/init/component` | 仅导入组件集 |
| POST | `/api/init/icon` | 仅导入 SVG + 插画 |
| POST | `/api/init/template` | 仅导入模版 |

#### 各类型入库流程

**组件集**

1. 读 `storage/component/component_map.json`，格式：
   ```json
   [{ "indexPath": "component/ICT_UI/component_index.json", ... }]
   ```
2. 按 `indexPath` 找到对应的 `component_index.json`，格式：
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
3. 以 variant 为粒度，每条写 `resources`（upsert key: `name + resource_type`）+ `component_variants`（upsert key: `variant_key`）

**SVG / 插画**

读 `storage/icon/icons.json` / `storage/illus/illus.json`，格式：
```json
[{ "id": 100, "name": "首页", "englishName": "home", "category": "navigation", "description": "..." }]
```
每条写 `resources`（upsert key: `name + resource_type`）+ `resource_icons`（upsert key: `resource_id`）

**模版**

读 `storage/template/templates.json`，每次都 create（不幂等），只写 `resources`。

### Mock 模式

`.env` 中 `USE_MOCK=true` 时，`clients/external.py` 返回模拟数据，不调用任何外部接口，用于本地开发。

---

## 前端结构

```
lib-resource-ui/src/
├── App.tsx          # 布局 + 左侧导航，页面切换
└── pages/
    ├── ResourceOverview.tsx    # 数据总览（调 /api/resources/categories）
    ├── ComponentManage.tsx     # 组件集管理
    ├── TemplateManage.tsx      # 模版管理
    ├── SVGManage.tsx           # SVG 管理
    ├── IllustrationManage.tsx  # 插画管理
    └── ImageManage.tsx         # 图片管理
```

前端开发服务器（port 5173）已配置代理：`/api` 和 `/static` → `http://localhost:8009`。

---

## 常见改动指引

| 改动 | 要动哪些文件 |
|------|-------------|
| 加新资源类型 | `enums.py` 加枚举 → `models/resource.py` 按需加字段 → 新建 router + service + schema |
| 加/改 API 字段 | `models/resource.py`（ORM） → `schemas/resource.py`（Pydantic） → `routers/resources.py` 的 `_fmt()` |
| 加/改组件结构化字段 | `models/resource.py` 的 `ComponentVariant` → `services/init_service.py` 的 `_upsert_component_variant` |
| 加/改图标结构化字段 | `models/resource.py` 的 `ResourceIcon` → `services/init_service.py` 的 `_upsert_resource_icon` |
| 修改初始化逻辑 | `services/init_service.py` |
| 修改外部 API 对接 | `clients/external.py`（Mock 和真实实现都在这里） |
| 加前端页面 | `pages/` 下新建 → `App.tsx` 注册导航和路由 |

---

## 环境配置速查

```env
DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD  # MySQL（留空 DB_URL 时生效）
DB_URL=sqlite:///./dev.db                             # 本地 SQLite 快速启动
FILE_ROOT_DIR=./storage                               # 文件存储根目录
USE_MOCK=true                                         # 本地开发不调外部 API
```

启动命令：
```bash
# 后端
cd lib-resource-service && uvicorn app.main:app --reload --port 8009

# 前端
cd lib-resource-ui && npm run dev
```
