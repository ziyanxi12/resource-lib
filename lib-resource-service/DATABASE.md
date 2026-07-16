# 数据库表结构文档

本文档详细说明后端数据库表结构，与 `app/models/resource.py` ORM 定义保持同步。

---

## 一、表结构总览

```
resources (主表)
    │
    ├─ N:1 ── resource_sources   source_id → resource_sources.id
    ├─ N:1 ── resource_groups    group_id → resource_groups.id
    └─ 1:N ── resource_tags      resource_id → resources.id
```

**表数量：** 4 张表

| 表名 | 说明 |
|------|------|
| `resources` | 资源主表（通用字段） |
| `resource_tags` | 标签表（多对多） |
| `resource_sources` | 来源表（数据来源管理） |
| `resource_groups` | 分组表（树形分类结构） |

---

## 二、各表字段清单

### 1. `resources` - 资源主表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | PK, 自增 | - | 主键，全局唯一 |
| `resource_type` | SmallInteger | NOT NULL | - | 资源类型：1=组件 2=模版 3=图标 4=插画 5=图片 6=文件 |
| `source_id` | Integer | FK, NOT NULL | - | 来源ID，关联 resource_sources.id |
| `name` | String(255) | NOT NULL | - | 资源名称 |
| `description` | Text | NULL | - | 描述文本 |
| `search_text` | Text | NULL | - | 业务搜索关键词 |
| `vector_text` | Text | NULL | - | 向量文本（四个字段拼接） |
| `file_name` | String(255) | NULL | - | 文件名，如 abc.svg |
| `file_url` | String(500) | NULL | - | 文件链接（外部） |
| `file_path` | String(500) | NULL | - | 文件相对路径，如 icon/abc.svg |
| `file_size` | Integer | NULL | - | 文件大小（bytes） |
| `file_type` | String(50) | NULL | - | 文件类型（后缀） |
| `width` | Float | NULL | - | 资源宽度（px） |
| `height` | Float | NULL | - | 资源高度（px） |
| `thumbnail_path` | String(500) | NULL | - | 缩略图路径 |
| `raw_data` | JSON | NULL | - | 原始数据 JSON |
| `group_id` | Integer | FK | NULL | 所属分组ID，关联 resource_groups.id |
| `created_by` | String(100) | NULL | - | 创建者 |
| `is_deleted` | Integer | NOT NULL | 0 | 软删除标记：0=正常 1=已删除 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |
| `data_updated_at` | DateTime | NULL | - | 业务数据更新时间，用于向量同步判断 |
| `vector_updated_at` | DateTime | NULL | - | 向量库更新时间 |

**外键关系：**
- `source_id` → `resource_sources.id`（RESTRICT：禁止删除有资源的来源）
- `group_id` → `resource_groups.id`（SET NULL：删除分组时置空）

---

### 2. `resource_tags` - 标签表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | PK, 自增 | - | 主键 |
| `resource_id` | Integer | FK, NOT NULL | - | 外键→resources.id，级联删除 |
| `tag` | String(100) | NOT NULL | - | 标签内容 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |

**说明：**
- 一个资源可以有多个标签（1:N关系）
- 删除资源时自动删除所有标签（CASCADE）

---

### 3. `resource_sources` - 来源表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | PK, 自增 | - | 主键 |
| `code` | String(50) | UNIQUE, NOT NULL | - | 来源代码，如 figma, manual, api_sync |
| `name` | String(255) | NOT NULL | - | 来源名称 |
| `resource_type` | SmallInteger | NOT NULL | - | 关联资源类型 |
| `is_sync_source` | Integer | NOT NULL | 0 | 是否同步来源：0=否 1=是 |
| `config` | JSON | NULL | - | 来源配置（API 地址、认证信息等） |
| `is_active` | Integer | NOT NULL | 1 | 是否启用：0=否 1=是 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 管理数据来源（Figma、手工上传、API 同步等）
- 每个来源关联一种资源类型
- `is_sync_source=1` 表示该来源支持自动同步

---

### 4. `resource_groups` - 分组表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | PK, 自增 | - | 主键 |
| `resource_type` | SmallInteger | NOT NULL | - | 资源类型：1-6 对应六类资源 |
| `source_id` | Integer | FK | NULL | 来源ID（分组按来源独立） |
| `name` | String(255) | NOT NULL | - | 分组名称 |
| `parent_id` | Integer | FK | NULL | 父分组ID，NULL表示根节点 |
| `level` | SmallInteger | NOT NULL | 0 | 层级深度：0=根节点 |
| `real_path` | String(500) | NOT NULL | - | 完整路径：根分组/一级分组/二级分组 |
| `sort_order` | Integer | NOT NULL | 0 | 同级排序序号 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 树形结构，每种资源类型+来源有独立的分组树
- `parent_id` 自引用实现树形结构
- `real_path` 存储完整路径便于查询展示

---

## 三、资源类型枚举

定义位置：`app/enums.py`

| 值 | 名称 | 中文标签 |
|----|------|----------|
| 1 | component | 组件集 |
| 2 | template | 模版 |
| 3 | icon | SVG |
| 4 | illus | 插画 |
| 5 | image | 图片 |
| 6 | file | 文件 |

---

## 四、索引与约束

### 主表索引
```sql
PRIMARY KEY (id)
INDEX idx_resource_type (resource_type)
INDEX idx_source_id (source_id)
INDEX idx_group_id (group_id)
INDEX idx_is_deleted (is_deleted)
```

### 标签表索引
```sql
PRIMARY KEY (id)
INDEX idx_resource_id (resource_id)
```

### 来源表索引
```sql
PRIMARY KEY (id)
UNIQUE INDEX idx_code (code)
INDEX idx_resource_type (resource_type)
```

### 分组表索引
```sql
PRIMARY KEY (id)
INDEX idx_resource_type (resource_type)
INDEX idx_source_id (source_id)
INDEX idx_parent_id (parent_id)
```

---

## 五、数据 API 返回格式

### 5.1 数据流转链路

```
数据库 (resources表)
    ↓ SQLAlchemy ORM查询
Resource 对象 (models/resource.py)
    ↓ _fmt() 函数处理 (routers/resources.py:177-203)
JSON 响应
    ↓ 前端 api.ts 请求
前端 item 对象
```

### 5.2 `_fmt()` 函数字段映射

位置：`app/routers/resources.py:177-203`

| 前端字段 | 数据来源 | 处理方式 |
|----------|----------|----------|
| `id` | `r.id` | 直接取值 |
| `resource_type` | `r.resource_type` | 直接取值 |
| `resource_type_name` | `r.resource_type` | `ResourceType(r.resource_type).name` 枚举转名称 |
| `source_id` | `r.source_id` | 直接取值 |
| `name` | `r.name` | 直接取值 |
| `description` | `r.description` | 直接取值 |
| `search_text` | `r.search_text` | 直接取值 |
| `vector_text` | `r.vector_text` | 直接取值 |
| `file_name` | `r.file_name` | 直接取值 |
| `file_url` | `r.file_url` | 直接取值 |
| `file_path` | `r.file_path` | 直接取值 |
| `file_size` | `r.file_size` | 直接取值 |
| `file_type` | `r.file_type` | 直接取值 |
| `width` | `r.width` | 直接取值 |
| `height` | `r.height` | 直接取值 |
| `thumbnail_path` | `r.thumbnail_path` | 直接取值 |
| `raw_data` | `r.raw_data` | 直接取值 |
| `group_id` | `r.group_id` | 直接取值 |
| `created_by` | `r.created_by` | 直接取值 |
| `created_at` | `r.created_at` | `.isoformat()` 转 ISO 字符串 |
| `updated_at` | `r.updated_at` | `.isoformat()` 转 ISO 字符串 |
| `data_updated_at` | `r.data_updated_at` | `.isoformat()` 转 ISO 字符串 |
| `vector_updated_at` | `r.vector_updated_at` | `.isoformat()` 转 ISO 字符串 |
| `tags` | `r.tags` | `[t.tag for t in r.tags]` 提取标签名列表 |

### 5.3 处理逻辑总结

**直接取值字段**：大部分字段直接从 ORM 对象取值，不做转换

**特殊处理字段**：
1. `resource_type_name`：枚举值转名称（如 `1` → `component`）
2. `tags`：从关联表 `resource_tags` 提取标签名字符串列表
3. 时间字段：`datetime` 对象通过 `.isoformat()` 转为 ISO 8601 格式字符串

---

## 六、向量文本构建

`vector_text` 字段由以下四个字段拼接而成：

1. `name` - 资源名称
2. `description` - 描述文本
3. `tags` - 标签列表（拼接为字符串）
4. `search_text` - 业务搜索关键词

构建逻辑位于：`app/services/resource_service.py` 中的 `build_vector_text()` 函数

---

## 七、ORM 定义位置

所有表结构定义位于：`app/models/resource.py`

**对应关系：**
- `Resource` 类 → `resources` 表
- `ResourceTag` 类 → `resource_tags` 表
- `ResourceSource` 类 → `resource_sources` 表
- `ResourceGroup` 类 → `resource_groups` 表

---

## 八、修改历史

| 日期 | 修改内容 |
|------|---------|
| 2026-07-15 | 重写文档，反映 v2.0 数据库结构（新增 source/group 表，移除详情表） |