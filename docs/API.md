# 资源库管理服务 API 文档

## 一、接口概览

### 服务地址

- **开发环境**: `http://localhost:8009`
- **生产环境**: 替换为实际服务地址

### 通用说明

#### 认证

当前版本无认证，所有接口公开访问。

#### 分页

列表接口支持分页参数：
- `page`: 页码（从 1 开始）
- `limit`: 每页数量（默认 20，最大 100）

#### 时间格式

所有时间字段使用 ISO 8601 格式：`YYYY-MM-DDTHH:mm:ss`

#### 错误响应

错误时返回：
```json
{
  "detail": "错误描述信息"
}
```

---

## 二、资源类型管理

### GET /api/resource-types

获取所有资源类型定义。

**请求参数**: 无

**返回格式**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "component",
      "label": "组件集"
    },
    {
      "id": 2,
      "name": "template",
      "label": "模版"
    },
    {
      "id": 3,
      "name": "icon",
      "label": "SVG"
    },
    {
      "id": 4,
      "name": "illus",
      "label": "插画"
    },
    {
      "id": 5,
      "name": "image",
      "label": "图片"
    },
    {
      "id": 6,
      "name": "file",
      "label": "文件"
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 资源类型 ID（数据库存储值） |
| `name` | string | 资源类型名（API 参数使用） |
| `label` | string | 中文展示名称 |

**调用示例**:
```bash
curl http://localhost:8009/api/resource-types
```

---

## 三、来源管理

来源（Source）用于标识资源的来源，每个资源必须关联一个来源。

### GET /api/sources

获取来源列表。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | 资源类型名筛选（component/template/icon/illus/image/file） |
| `is_active` | int | 否 | 是否启用筛选（0=否，1=是） |

**返回格式**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "手动上传-图标",
      "resource_type": 3,
      "is_sync_source": 0,
      "config": null,
      "is_active": 1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 来源 ID |
| `name` | string | 来源名称 |
| `resource_type` | int | 关联的资源类型 ID |
| `is_sync_source` | int | 是否同步来源（0=否，1=是） |
| `config` | object | 来源配置（JSON） |
| `is_active` | int | 是否启用（0=否，1=是） |
| `created_at` | string | 创建时间 |
| `updated_at` | string | 更新时间 |

**调用示例**:
```bash
# 获取所有来源
curl http://localhost:8009/api/sources

# 筛选图标类型来源
curl "http://localhost:8009/api/sources?type=icon"
```

---

### POST /api/sources

创建来源。

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 来源名称 |
| `type` | string | 是 | 资源类型名（component/template/icon/illus/image/file） |
| `is_sync_source` | int | 否 | 是否同步来源，默认 0 |
| `config` | object | 否 | 来源配置（JSON） |
| `is_active` | int | 否 | 是否启用，默认 1 |

**返回格式**: 返回创建的来源对象（同 GET 返回字段）

**调用示例**:
```bash
curl -X POST http://localhost:8009/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "手动上传-图标",
    "type": "icon",
    "is_sync_source": 0,
    "is_active": 1
  }'
```

---

### PUT /api/sources/{id}

更新来源。

**路径参数**:
- `id`: 来源 ID

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 来源名称 |
| `is_sync_source` | int | 否 | 是否同步来源 |
| `config` | object | 否 | 来源配置 |
| `is_active` | int | 否 | 是否启用 |

**返回格式**: 返回更新后的来源对象

**调用示例**:
```bash
curl -X PUT http://localhost:8009/api/sources/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "新名称"}'
```

---

### DELETE /api/sources/{id}

删除来源。

**路径参数**:
- `id`: 来源 ID

**返回格式**:
```json
{
  "message": "删除成功"
}
```

**调用示例**:
```bash
curl -X DELETE http://localhost:8009/api/sources/1
```

**注意**: 如果来源下还有资源，删除会失败（外键约束）。

---

## 四、分组管理

分组按来源独立，每种资源类型 + 来源有独立的分组树。

### GET /api/groups

获取分组树。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型名（component/template/icon/illus/image/file） |
| `source_id` | int | 否 | 来源 ID 筛选 |
| `exclude_default` | bool | 否 | 是否排除默认分组，默认 true |

**返回格式**:
```json
{
  "resource_type": 3,
  "resource_type_name": "icon",
  "source_id": 1,
  "items": [
    {
      "id": 1,
      "name": "导航图标",
      "parent_id": null,
      "level": 0,
      "real_path": "导航图标",
      "sort_order": 0,
      "is_default": 0,
      "children": [
        {
          "id": 2,
          "name": "方向箭头",
          "parent_id": 1,
          "level": 1,
          "real_path": "导航图标/方向箭头",
          "sort_order": 0,
          "is_default": 0,
          "children": []
        }
      ]
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 分组 ID |
| `name` | string | 分组名称 |
| `parent_id` | int | 父分组 ID（null 表示根节点） |
| `level` | int | 层级深度（0=根节点） |
| `real_path` | string | 完整路径（如"导航图标/方向箭头"） |
| `sort_order` | int | 同级排序序号 |
| `is_default` | int | 是否默认分组 |
| `children` | array | 子分组列表 |

**调用示例**:
```bash
curl "http://localhost:8009/api/groups?type=icon&source_id=1"
```

---

### POST /api/groups

创建分组。

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型名 |
| `name` | string | 是 | 分组名称 |
| `source_id` | int | 否 | 来源 ID |
| `parent_id` | int | 否 | 父分组 ID（null 表示根节点） |

**返回格式**: 返回创建的分组对象

**调用示例**:
```bash
curl -X POST http://localhost:8009/api/groups \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "name": "导航图标",
    "source_id": 1
  }'
```

---

### PUT /api/groups/{id}

更新分组名称。

**路径参数**:
- `id`: 分组 ID

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 新的分组名称 |

**调用示例**:
```bash
curl -X PUT http://localhost:8009/api/groups/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "新名称"}'
```

---

### DELETE /api/groups/{id}

删除分组。

**路径参数**:
- `id`: 分组 ID

**返回格式**:
```json
{
  "id": 1,
  "message": "删除成功"
}
```

**注意**: 删除分组时，分组下的资源会移动到默认分组。

---

### PUT /api/groups/{id}/move

移动分组（调整父节点和排序）。

**路径参数**:
- `id`: 分组 ID

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `parent_id` | int | 否 | 新的父分组 ID（null 表示移动到根节点） |
| `sort_order` | int | 否 | 新的排序序号 |

**调用示例**:
```bash
curl -X PUT http://localhost:8009/api/groups/2/move \
  -H "Content-Type: application/json" \
  -d '{"parent_id": 1, "sort_order": 0}'
```

---

### PUT /api/groups/reorder

批量重排序分组。

**请求参数（Body）**:
```json
{
  "items": [
    {"id": 1, "sort_order": 0},
    {"id": 2, "sort_order": 1}
  ]
}
```

**调用示例**:
```bash
curl -X PUT http://localhost:8009/api/groups/reorder \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": 1, "sort_order": 0},
      {"id": 2, "sort_order": 1}
    ]
  }'
```

---

## 五、资源管理

### GET /api/resources

获取资源列表。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | 资源类型名筛选 |
| `source_id` | int | 否 | 来源 ID 筛选 |
| `group_id` | int | 否 | 分组 ID 筛选 |
| `search` | string | 否 | 搜索关键词（匹配名称/描述/search_text） |
| `page` | int | 否 | 页码，默认 1 |
| `limit` | int | 否 | 每页数量，默认 20，最大 100 |

**返回格式**:
```json
{
  "total": 100,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "id": 1,
      "resource_type": 3,
      "resource_type_name": "icon",
      "source_id": 1,
      "name": "首页图标",
      "description": "首页导航图标",
      "search_text": "首页 home",
      "vector_text": "首页图标 首页导航图标 首页 home",
      "file_name": "home.svg",
      "file_path": "icon/home.svg",
      "file_size": 1024,
      "file_type": "svg",
      "width": 24,
      "height": 24,
      "thumbnail_path": "image/home_thumb.png",
      "raw_data": null,
      "group_id": 1,
      "created_by": null,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "data_updated_at": "2024-01-01T00:00:00",
      "vector_updated_at": "2024-01-01T00:00:00",
      "tags": ["导航", "首页"]
    }
  ]
}
```

**调用示例**:
```bash
# 获取图标列表
curl "http://localhost:8009/api/resources?type=icon&page=1&limit=20"

# 搜索
curl "http://localhost:8009/api/resources?type=icon&search=按钮"
```

---

### GET /api/resources/{id}

获取单个资源详情。

**路径参数**:
- `id`: 资源 ID

**返回格式**: 返回单个资源对象（字段同列表返回）

**调用示例**:
```bash
curl http://localhost:8009/api/resources/1
```

---

### PUT /api/resources/{id}

更新资源元数据。

**路径参数**:
- `id`: 资源 ID

**请求参数（Form Data）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 资源名称 |
| `description` | string | 否 | 描述 |
| `tags` | string | 否 | 标签（JSON 数组字符串） |
| `group_id` | int | 否 | 分组 ID |
| `search_text` | string | 否 | 搜索关键词 |
| `file_name` | string | 否 | 文件名 |
| `thumbnail` | file | 否 | 缩略图文件 |
| `file` | file | 否 | 资源文件 |

**返回格式**:
```json
{
  "message": "更新成功",
  "id": 1
}
```

**调用示例**:
```bash
# 更新名称
curl -X PUT http://localhost:8009/api/resources/1 \
  -F "name=新名称"

# 更新标签
curl -X PUT http://localhost:8009/api/resources/1 \
  -F 'tags=["标签1","标签2"]'

# 更新缩略图
curl -X PUT http://localhost:8009/api/resources/1 \
  -F "thumbnail=@/path/to/thumbnail.png"
```

---

### DELETE /api/resources/{id}

删除资源（软删除）。

**路径参数**:
- `id`: 资源 ID

**返回格式**:
```json
{
  "message": "删除成功",
  "id": 1
}
```

**调用示例**:
```bash
curl -X DELETE http://localhost:8009/api/resources/1
```

---

### DELETE /api/resources/batch

批量删除资源。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型名 |
| `source_id` | int | 否 | 来源 ID 筛选 |
| `group_id` | int | 否 | 分组 ID 筛选 |

**返回格式**:
```json
{
  "deleted": 10
}
```

**调用示例**:
```bash
curl -X DELETE "http://localhost:8009/api/resources/batch?type=icon&source_id=1"
```

---

### POST /api/resources/{id}/understand

对资源的预览图生成语义描述。

**路径参数**:
- `id`: 资源 ID

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | 否 | 引导生成方向的提示词 |

**返回格式**:
```json
{
  "id": 1,
  "description": "这是一个蓝色的按钮图标，带有圆角边框"
}
```

**调用示例**:
```bash
curl -X POST http://localhost:8009/api/resources/1/understand \
  -H "Content-Type: application/json" \
  -d '{"prompt": "描述这个图标的用途"}'
```

**注意**: 该接口耗时约 10-30 秒。

---

### POST /api/resources/sync-vectors

批量同步向量数据。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型名 |
| `source_id` | int | 否 | 来源 ID 筛选 |

**返回格式**:
```json
{
  "total": 100,
  "synced": 98,
  "failed": 2,
  "skipped": 0,
  "message": "同步完成"
}
```

**调用示例**:
```bash
curl -X POST "http://localhost:8009/api/resources/sync-vectors?type=icon"
```

---

### GET /api/resources/categories

获取所有有数据的资源类别及各自的数量。

**返回格式**:
```json
{
  "categories": [
    {"type": "icon", "count": 500},
    {"type": "component", "count": 120}
  ]
}
```

**调用示例**:
```bash
curl http://localhost:8009/api/resources/categories
```

---

## 六、文件上传

### POST /api/upload

统一批量上传接口。

**请求参数**:
- Query 参数 `type`: 资源类型名（component/template/icon/illus/image/file）
- Form Data 参数:
  - `files`: 资源文件列表
  - `thumbnails`: 缩略图列表（PNG 格式）
  - `items`: JSON 字符串，包含元数据数组
  - `source_id`: 来源 ID（必填）
  - `created_by`: 创建者（可选）

**items 格式**:
```json
[
  {
    "name": "图标名称",
    "group_id": 1,
    "width": 24,
    "height": 24
  }
]
```

**返回格式**:
```json
{
  "success": true,
  "count": 10,
  "items": [
    {
      "id": 1,
      "name": "图标名称",
      "file_path": "icon/abc.svg",
      "thumbnail_path": "image/abc_thumb.png"
    }
  ],
  "message": "上传成功"
}
```

**调用示例**:
```bash
curl -X POST "http://localhost:8009/api/upload?type=icon" \
  -F "files=@icon1.svg" \
  -F "files=@icon2.svg" \
  -F "thumbnails=@thumb1.png" \
  -F "thumbnails=@thumb2.png" \
  -F 'items=[{"name":"图标1","group_id":1},{"name":"图标2","group_id":1}]' \
  -F "source_id=1"
```

**注意**:
- files、thumbnails、items 必须一一对应（索引对应）
- 缩略图必须为 PNG 格式

---

## 七、向量搜索

### POST /api/vector/search

向量搜索（支持批量、三种响应模式）。

**请求参数（Body）**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | - | 资源类型名（component/template/icon/illus/image/file） |
| `queries` | array | 是 | - | 批量搜索文本数组 |
| `mode` | string | 否 | `hybrid` | 搜索模式（hybrid/sparse/dense） |
| `top_k` | int | 否 | 10 | 每个 query 返回数量 |
| `filters` | object | 否 | - | 过滤条件（如 {source_id: 1, group_id: 2}） |
| `response_mode` | string | 否 | `complete` | 响应模式（basic/normal/complete） |
| `hybrid_weight` | float | 否 | 0.7 | 混合搜索权重 |

**返回格式**:

```json
{
  "results": [
    [
      // 第一个 query 的结果
      {
        "id": 1,
        "name": "首页图标",
        "score": 0.95,
        // ... 其他字段（根据 response_mode）
      }
    ]
  ]
}
```

**响应模式说明**:

| 模式 | 返回字段 | 使用场景 |
|------|---------|----------|
| `basic` | `id`, `vector_text`, `score` | LLM 专用 |
| `normal` | `id`, `vector_text`, `score`, `raw_data` | 外部系统调用 |
| `complete` | 全量字段（30+ 字段） | 前端展示（默认） |

**调用示例**:

```bash
# basic 模式（LLM 专用）
curl -X POST http://localhost:8009/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "queries": ["按钮"],
    "top_k": 10,
    "response_mode": "basic"
  }'

# normal 模式（外部系统）
curl -X POST http://localhost:8009/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "queries": ["按钮"],
    "top_k": 10,
    "response_mode": "normal"
  }'

# complete 模式（前端展示，默认）
curl -X POST http://localhost:8009/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "queries": ["按钮"],
    "top_k": 10,
    "response_mode": "complete"
  }'

# 带 filters 的搜索
curl -X POST http://localhost:8009/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "queries": ["按钮"],
    "top_k": 10,
    "filters": {"source_id": 1}
  }'

# 批量搜索
curl -X POST http://localhost:8009/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "type": "icon",
    "queries": ["按钮", "输入框"],
    "top_k": 5
  }'
```

---

### POST /api/vector/search/llm

LLM 精简版搜索，专为 AI/LLM 设计。

**请求参数**: 同 `/api/vector/search`

**返回格式**:
```json
{
  "results": [
    [
      {
        "data_id": "123",
        "vector_text": "首页图标 首页导航图标",
        "score": 0.95
      }
    ]
  ]
}
```

**说明**: 详细使用方式见 [LLM_VECTOR_API.md](../lib-resource-service/LLM_VECTOR_API.md)

---

### GET /api/vector/detail

通过 data_id + type 获取全量资源数据。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型名 |
| `data_id` | string | 是 | 向量库唯一标识 |

**返回格式**: 返回完整资源对象（同 GET /api/resources/{id}）

**调用示例**:
```bash
curl "http://localhost:8009/api/vector/detail?type=icon&data_id=123"
```

---

### GET /api/vector/missing/{resource_type}

检测指定资源类型的向量缺失情况。

**路径参数**:
- `resource_type`: 资源类型 ID（1-6）

**返回格式**:
```json
{
  "resource_type": "icon",
  "db_count": 500,
  "vector_count": 495,
  "missing_count": 5,
  "missing_ids": [1, 2, 3, 4, 5]
}
```

**调用示例**:
```bash
curl http://localhost:8009/api/vector/missing/3
```

---

### POST /api/vector/rebuild

全量重建向量库。

**请求参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `resource_type` | int | 是 | 资源类型 ID（1-6） |

**返回格式**:
```json
{
  "resource_type": "icon",
  "total": 500,
  "synced": 500,
  "failed": 0,
  "message": "同步完成"
}
```

**调用示例**:
```bash
curl -X POST "http://localhost:8009/api/vector/rebuild?resource_type=3"
```

---

### POST /api/vector/sync

精准补录缺失的向量数据（基于时间戳）。

**请求参数（Query）**: 同 rebuild

**调用示例**:
```bash
curl -X POST "http://localhost:8009/api/vector/sync?resource_type=3"
```

---

## 八、初始化

### POST /api/init

初始化全部资源（从 storage/ 目录读取预置文件批量入库）。

**返回格式**:
```json
{
  "message": "初始化完成"
}
```

**调用示例**:
```bash
curl -X POST http://localhost:8009/api/init
```

---

### POST /api/init/component

初始化组件集资源。

---

### POST /api/init/icon

初始化图标和插画资源。

---

### POST /api/init/template

初始化模版资源。

---

## 九、错误码

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |
| 502 | 向量服务调用失败 |
| 503 | 向量服务未启用 |

### 常见错误信息

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `未知资源类型: xxx` | type 参数错误 | 使用正确的类型名：component/template/icon/illus/image/file |
| `无效的 response_mode: xxx` | response_mode 参数错误 | 使用：basic/normal/complete |
| `来源不存在` | source_id 无效 | 检查来源 ID 是否正确 |
| `分组不存在` | group_id 无效 | 检查分组 ID 是否正确 |
| `queries 不能为空` | 向量搜索缺少 queries 参数 | 添加搜索关键词数组 |
| `向量服务未启用` | 向量服务未启动 | 检查 VECTOR_SERVICE_ENABLED 配置 |
| `向量服务调用失败` | 向量服务异常 | 检查向量服务状态 |

---

## 十、附录

### 资源类型枚举

| ID | Name | Label | 说明 |
|----|------|-------|------|
| 1 | component | 组件集 | UI 组件集 |
| 2 | template | 模版 | 页面模版 |
| 3 | icon | SVG | SVG 图标 |
| 4 | illus | 插画 | 插画素材 |
| 5 | image | 图片 | 图片素材 |
| 6 | file | 文件 | 通用文件 |

### 静态文件访问

上传的文件可通过静态文件服务访问：
```
GET /static/{file_path}
```

示例：
```bash
curl http://localhost:8009/static/icon/home.svg
```

### 健康检查

```
GET /health
```

返回：
```json
{
  "status": "ok",
  "mode": "mock"
}
```

---

## 更多信息

- **LLM 专用 API**: 见 [LLM_VECTOR_API.md](../lib-resource-service/LLM_VECTOR_API.md)
- **项目文档**: 见 [CLAUDE.md](../CLAUDE.md)
- **数据库结构**: 见 [DATABASE.md](../lib-resource-service/DATABASE.md)