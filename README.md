# lib-resource 资源库管理系统

统一管理五类设计资源：组件集、模版、SVG、插画、图片。

## 项目结构

```
lib-resource/
├── lib-resource-service/       # 后端（Python FastAPI）
│   ├── storage/                # 文件存储根目录（component/icon/template/image）
│   ├── app/                    # 业务代码
│   ├── requirements.txt
│   └── .env                    # 环境变量（从 .env.example 复制后填写）
└── lib-resource-ui/            # 前端（React + Vite）
```

---

## 环境要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.9+ | 后端运行时 |
| Node.js | 18+ | 前端构建工具 |
| npm | 9+ | 前端包管理 |
| MySQL | 5.7+ / 8.0+ | 数据库 |

> 当前开发环境：Python 3.9.6、Node.js 24.14.0、npm 11.9.0

---

## 后端部署

### 1. 准备 MySQL 数据库

连接到 MySQL，执行以下 SQL：

```sql
CREATE DATABASE resource_lib CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

如需单独建用户（不使用 root）：

```sql
CREATE USER 'resource'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON resource_lib.* TO 'resource'@'%';
FLUSH PRIVILEGES;
```

### 2. 配置环境变量

进入后端目录，复制示例文件并填写配置：

```bash
cd lib-resource-service
cp .env.example .env
```

编辑 `.env`，填写 MySQL 连接信息：

```env
# 服务端口
PORT=8009

# MySQL 连接（不需要设置 DB_URL，留空即可）
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=resource_lib
DB_USER=root
DB_PASSWORD=你的密码

# 文件存储根目录（component/icon/template/image 子目录均在此下）
FILE_ROOT_DIR=./storage

# 组件库映射表（位于 storage/component/ 下）
COMPONENT_MAP_FILE=./storage/component/component_map.json

# Mock 模式：true = 不调用真实外部 API（本地开发用）
USE_MOCK=true
```

### 3. 安装依赖

```bash
cd lib-resource-service
pip install -r requirements.txt
```

主要依赖版本：

| 包 | 版本 |
|----|------|
| fastapi | 0.115.0 |
| uvicorn | 0.30.6 |
| sqlalchemy | 2.0.35 |
| pymysql | 1.1.1 |
| pydantic | 2.9.2 |
| python-dotenv | 1.0.1 |
| python-multipart | 0.0.12 |
| httpx | 0.27.2 |
| Pillow | 10.4.0 |

### 4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload
```

服务启动时会自动在 MySQL 中创建所需的数据表（`resources`、`resource_tags`），**无需手动建表**。

启动成功后：
- API 服务：`http://localhost:8009`
- 接口文档：`http://localhost:8009/docs`
- 健康检查：`http://localhost:8009/health`

---

## 前端部署

### 1. 安装依赖

```bash
cd lib-resource-ui
npm install
```

主要依赖版本：

| 包 | 版本 |
|----|------|
| react | ^18.3.1 |
| antd | ^5.21.6 |
| @ant-design/icons | ^5.4.0 |
| vite | ^5.4.0 |
| typescript | ^5.5.3 |

### 2. 启动开发服务

```bash
npm run dev
```

前端默认运行在 `http://localhost:5173`，已配置代理将 `/api` 和 `/static` 请求转发到后端 `http://localhost:8009`。

### 3. 生产构建

```bash
npm run build
```

构建产物输出到 `dist/` 目录，部署到任意静态文件服务器即可。

> 生产环境部署时，需确保 Nginx 或其他服务器将 `/api` 和 `/static` 请求代理到后端服务。

---

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/resources/categories` | 各类别数据量统计 |
| GET | `/api/resources/all?type_id=3` | 指定类别全量数据 |
| GET | `/api/resources` | 资源列表（支持类型/搜索/分页） |
| GET | `/api/resources/{id}` | 单个资源详情 |
| PUT | `/api/resources/{id}` | 更新资源元数据 |
| DELETE | `/api/resources/{id}` | 删除资源 |
| GET | `/api/component/list` | 组件库列表 |
| POST | `/api/component/sync` | 同步组件集 |
| POST | `/api/template/upload` | 上传模版 |
| POST | `/api/icon/sync` | 同步 SVG / 插画 |
| POST | `/api/image/upload` | 上传图片 |
| POST | `/api/init` | 初始化导入全部类型 |
| POST | `/api/init/component` | 初始化导入组件集 |
| POST | `/api/init/icon` | 初始化导入 SVG + 插画 |
| POST | `/api/init/template` | 初始化导入模版 |
| GET | `/health` | 服务健康检查 |

`type_id` 对照表：`1` 组件集 / `2` 模版 / `3` SVG / `4` 插画 / `5` 图片

---

## 数据库表结构

### resources（资源主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| resource_type | SMALLINT | 1=组件集 2=模版 3=SVG 4=插画 5=图片 |
| name | VARCHAR(255) | 资源名称 |
| file_name | VARCHAR(255) | 文件名，如 `abc.svg` |
| file_path | VARCHAR(500) | 文件相对路径，如 `icon/abc.svg` |
| file_size | INT | 文件大小（bytes） |
| mime_type | VARCHAR(100) | MIME 类型，如 `image/png` |
| thumbnail_path | VARCHAR(500) | 缩略图相对路径 |
| dimensions | JSON | 尺寸，如 `{"width": 100, "height": 100}` |
| description | TEXT | 描述 |
| raw_data | TEXT | 原始数据 JSON 字符串 |
| created_by | VARCHAR(100) | 上传人 |
| is_deleted | INT | 软删除：0=正常 1=已删除 |
| sort_order | INT | 排序权重，越大越靠前 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### resource_tags（资源标签表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| resource_id | INT | 关联 resources.id |
| tag | VARCHAR(100) | 标签名 |
| created_at | DATETIME | 创建时间 |
