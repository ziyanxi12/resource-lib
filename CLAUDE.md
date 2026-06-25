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
│   │   └── resource.py      # ORM：Resource 主表 + ResourceTag 标签表
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
│   │   ├── svg.json          # SVG 初始化数据
│   │   └── illustration.json # 插画初始化数据
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

### resources 主表关键字段

| 字段 | 说明 |
|------|------|
| `resource_type` | 1=组件集 2=模版 3=SVG 4=插画 5=图片 |
| `name` | 资源名称（与 resource_type 组合作为 upsert key） |
| `file_name` | 文件名，如 `abc.svg` |
| `file_path` | 相对于 FILE_ROOT_DIR 的路径 |
| `raw_data` | 外部 API 返回的原始 JSON 字符串 |
| `is_deleted` | 软删除，0=正常 1=已删除 |

---

## 核心逻辑约定

### upsert vs create

- **同步类**（组件、图标、插画）→ 用 `upsert_resource(db, data)`，以 `(name, resource_type)` 做幂等更新
- **上传类**（图片、模版）→ 用 `create_resource(db, data)`，每次上传都是新记录

### 初始化入库（`/api/init`）

从 `storage/` 读预置 JSON 文件写入数据库，**不调用外部 API**：
- 组件集：读 `storage/component/component_map.json`，按每条记录的 `indexPath` 定位对应的 `component_index.json`，以 variant 为粒度入库
- SVG/插画：`storage/icon/svg.json` / `storage/icon/illustration.json`
- 模版：`storage/template/templates.json`

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
