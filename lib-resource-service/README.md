# lib-resource-service

资源库管理服务（Python / FastAPI），统一管理六类设计资源：组件集、模版、SVG、插画、图片、文件。

---

## 目录结构

```
lib-resource-service/
├── app/
│   ├── main.py               # 入口：注册路由、启动建表、静态文件服务
│   ├── config.py             # 所有配置项（从 .env 读取）
│   ├── database.py           # 数据库连接（SQLite / MySQL 二选一）
│   ├── enums.py              # ResourceType 枚举，DB 整数 ↔ API 字符串
│   ├── models/
│   │   └── resource.py       # ORM 表定义（resources / resource_tags / resource_sources / resource_groups）
│   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── resource.py       # 通用资源请求/响应
│   │   ├── source.py         # 来源管理
│   │   ├── group.py          # 分组管理
│   │   └── upload.py         # 批量上传响应
│   ├── clients/
│   │   ├── external.py       # 所有外部 API 调用（Mock 开关）
│   │   └── vector_client.py  # 向量服务客户端
│   ├── services/             # 业务逻辑
│   │   ├── resource_service.py   # 通用 CRUD
│   │   ├── upload_service.py     # 统一批量上传
│   │   ├── source_service.py     # 来源管理
│   │   ├── group_service.py      # 分组管理
│   │   ├── vector_sync_service.py # 向量同步
│   │   ├── vector_text_builder.py # 向量文本构建
│   │   └── init_service.py       # 初始化入库
│   └── routers/              # HTTP 路由
│       ├── resources.py      # 资源 CRUD
│       ├── upload.py         # 统一上传
│       ├── sources.py        # 来源管理
│       ├── group.py          # 分组管理
│       ├── search.py         # 向量搜索
│       ├── vector_router.py  # 向量服务代理
│       └── init_router.py    # 初始化入库
├── storage/                  # 文件存储根目录
│   ├── component/            # 组件集文件
│   ├── icon/                 # SVG 文件
│   ├── illus/                # 插画文件
│   ├── template/             # 模版文件
│   ├── image/                # 图片文件（含缩略图）
│   └── file/                 # 通用文件
├── requirements.txt
├── .env.example
├── DATABASE.md               # 数据库表结构文档
└── DESIGN.md                 # 完整设计文档
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
USE_MOCK=true                    # true=不调用真实外部 API
VECTOR_SERVICE_URL=http://localhost:8008
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

## 数据初始化

服务启动后，调用初始化接口将 `storage/` 下的预置文件批量写入数据库。

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/init` | 一次性导入全部类型 |
| POST | `/api/init/component` | 仅导入组件集 |
| POST | `/api/init/icon` | 仅导入 SVG + 插画 |
| POST | `/api/init/template` | 仅导入模版 |

---

## 主要 API

### 资源管理

```
GET    /api/resources              列表（?type=&source_id=&group_id=&search=&page=&limit=）
GET    /api/resources/{id}         详情
PUT    /api/resources/{id}         更新元数据
DELETE /api/resources/{id}         软删除
DELETE /api/resources/batch        批量删除（?type=&source_id=&group_id=）
POST   /api/resources/{id}/understand  语义理解
POST   /api/resources/sync-vectors     向量同步
```

### 统一上传

```
POST   /api/upload?type={icon|illus|template|image|file}
```

请求参数（multipart/form-data）：
- `files` - 资源文件列表
- `thumbnails` - 缩略图列表（PNG）
- `items` - JSON 字符串，元数据数组
- `source_id` - 来源ID（必填）

### 来源管理

```
GET    /api/sources                来源列表
POST   /api/sources                创建来源
PUT    /api/sources/{id}           更新来源
DELETE /api/sources/{id}           删除来源
```

### 分组管理

```
GET    /api/groups?type={type}&source_id={id}  分组树
POST   /api/groups                 创建分组
PUT    /api/groups/{id}            更新分组
DELETE /api/groups/{id}            删除分组
PUT    /api/groups/{id}/move       移动分组
```

### 向量搜索

```
POST   /api/vector/search
```

请求体：
```json
{
  "type": "component",
  "queries": ["蓝色按钮"],
  "mode": "hybrid",
  "top_k": 10
}
```

### 静态文件

```
GET    /static/{file_path}         访问上传文件
GET    /health                     健康检查
GET    /docs                       Swagger API 文档
```

---

## 核心设计

### 资源类型枚举

| 值 | 名称 | 中文 |
|----|------|------|
| 1 | component | 组件集 |
| 2 | template | 模版 |
| 3 | icon | SVG |
| 4 | illus | 插画 |
| 5 | image | 图片 |
| 6 | file | 文件 |

### 向量文本构建

```python
vector_text = name + description + tags + search_text
```

### 来源管理

每个资源必须关联一个来源（`source_id` 必填）。来源类型：
- 手动上传（manual_*）
- API 同步（api_*）
- Figma 同步（figma_*）

---

## 详细文档

- [DATABASE.md](./DATABASE.md) - 数据库表结构
- [DESIGN.md](./DESIGN.md) - 完整设计文档