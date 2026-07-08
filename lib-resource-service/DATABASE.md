# 数据库表结构文档

本文档详细说明后端数据库表结构，与 `app/models/resource.py` ORM 定义保持同步。

---

## 一、表结构总览

```
resources (主表)
    │
    ├─ 1:N ── resource_tags        resource_id → resources.id
    ├─ 1:1 ── component_variants   resource_id → resources.id (仅 resource_type=1)
    ├─ 1:1 ── resource_icons       resource_id → resources.id (仅 resource_type=3)
    └─ 1:1 ── resource_illus      resource_id → resources.id (仅 resource_type=4)
```

**表数量：** 5 张表
- `resources` - 资源主表（通用字段）
- `resource_tags` - 标签表（多对多）
- `component_variants` - 组件变体详情表
- `resource_icons` - SVG图标详情表
- `resource_illus` - 插画详情表

---

## 二、各表字段清单

### 1. `resources` - 资源主表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | PK, 自增 | - | 主键，全局唯一 |
| `resource_type` | SmallInteger | NOT NULL | - | 资源类型：1=组件 2=模版 3=图标 4=插画 5=图片 |
| `name` | String(255) | NOT NULL | - | 资源名称 |
| `file_name` | String(255) | NULL | - | 文件名，如 abc.svg |
| `file_path` | String(500) | NULL | - | 文件相对路径，如 icon/abc.svg |
| `file_size` | Integer | NULL | - | 文件大小（bytes） |
| `mime_type` | String(100) | NULL | - | MIME类型，如 image/png |
| `thumbnail_path` | String(500) | NULL | - | 缩略图路径 |
| `width` | Float | NULL | - | 资源宽度（px），可能为小数 |
| `height` | Float | NULL | - | 资源高度（px），可能为小数 |
| `description` | Text | NULL | - | 描述文本 |
| `raw_data` | Text | NULL | - | 原始数据 JSON 字符串 |
| `created_by` | String(100) | NULL | - | 创建者 |
| `is_deleted` | Integer | NOT NULL | 0 | 软删除标记：0=正常 1=已删除 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 使用 `resource_type` 字段区分五种资源类型
- 通用字段都在主表，特有字段在详情表
- `raw_data` 存储外部 API 返回的原始 JSON，用于向量构造等场景

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

### 3. `component_variants` - 组件变体详情表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `variant_key` | String(100) | PK | - | 变体key，来自Figma，全局唯一 |
| `resource_id` | Integer | FK, NOT NULL, UNIQUE | - | 外键→resources.id，级联删除，唯一约束 |
| `lib_file_key` | String(100) | NULL | - | **组件库文件key**（来自 component_map.json） |
| `lib_name` | String(255) | NULL | - | **组件库名称**（来自 component_map.json） |
| `canvas_name` | String(255) | NULL | - | 画布分组名，如"1.基础类" |
| `component_name` | String(255) | NULL | - | 组件集名称 |
| `component_guid` | String(100) | NULL | - | 组件集guid |
| `component_key` | String(100) | NULL | - | 组件集key，即parentKey |
| `name` | String(500) | NOT NULL | - | 变体属性字符串 |
| `guid` | String(100) | NULL, UNIQUE | - | 变体guid，唯一约束 |
| `component_props` | JSON | NULL | - | 变体属性列表，[{name, type}, ...] |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 仅用于 `resource_type=1`（组件）的资源
- 一个组件集可以有多个变体，按 `component_key` 分组
- `lib_file_key` 和 `lib_name` 来自 `component_map.json`，标识组件库来源

---

### 4. `resource_icons` - SVG图标详情表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `icon_id` | String(100) | PK | - | 图标原始id（来自JSON数据） |
| `resource_id` | Integer | FK, NOT NULL, UNIQUE | - | 外键→resources.id，级联删除，唯一约束 |
| `chinese_name` | String(255) | NULL | - | 中文名称 |
| `name` | String(255) | NULL | - | 英文全称，如 it_home |
| `english_name` | String(255) | NULL | - | 英文短名，如 home |
| `category` | String(100) | NULL | - | 分类，如 navigation, system |
| `group` | String(100) | NULL | - | 领域/分组 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 仅用于 `resource_type=3`（SVG图标）的资源
- `icon_id` 来自 `icons.json` 的原始数据

---

### 5. `resource_illus` - 插画详情表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `illus_id` | String(100) | PK | - | 插画原始id（来自JSON数据） |
| `resource_id` | Integer | FK, NOT NULL, UNIQUE | - | 外键→resources.id，级联删除，唯一约束 |
| `category` | String(100) | NULL | - | 分类 |
| `tags` | JSON | NULL | - | 标签列表，["空状态", "反馈"] |
| `version` | String(50) | NULL | - | 版本号 |
| `theme` | String(100) | NULL | - | 主题 |
| `created_at` | DateTime | NOT NULL | 当前时间 | 创建时间 |
| `updated_at` | DateTime | NOT NULL | 自动更新 | 更新时间 |

**说明：**
- 仅用于 `resource_type=4`（插画）的资源
- `illus_id` 来自 `illus.json` 的原始数据
- `tags` 是 JSON 数组，不同于 `resource_tags` 表（用于前端筛选）

---

## 三、主键策略

| 表 | 主键字段 | 策略 | 说明 |
|------|---------|------|------|
| `resources` | `id` | 自增 Integer | 全局唯一，用于关联 |
| `resource_tags` | `id` | 自增 Integer | 简单自增 |
| `component_variants` | `variant_key` | String(100) | 来自Figma，业务主键 |
| `resource_icons` | `icon_id` | String(100) | 来自JSON，业务主键 |
| `resource_illus` | `illus_id` | String(100) | 来自JSON，业务主键 |

---

## 四、索引与约束

### 主表索引
```sql
-- 隐式索引
PRIMARY KEY (id)

-- 应用层创建（SQLAlchemy auto create）
INDEX idx_resource_type (resource_type)
INDEX idx_is_deleted (is_deleted)
```

### 详情表索引
```sql
-- component_variants
PRIMARY KEY (variant_key)
UNIQUE INDEX idx_resource_id (resource_id)
UNIQUE INDEX idx_guid (guid)

-- resource_icons
PRIMARY KEY (icon_id)
UNIQUE INDEX idx_resource_id (resource_id)

-- resource_illus
PRIMARY KEY (illus_id)
UNIQUE INDEX idx_resource_id (resource_id)
```

---

## 五、字段使用说明

### 5.1 通用字段（所有资源类型）

| 字段 | 组件 | 模版 | SVG | 插画 | 图片 | 说明 |
|------|------|------|-----|------|------|------|
| `name` | ✓ | ✓ | ✓ | ✓ | ✓ | 资源名称（必填） |
| `file_name` | ✓ | ✓ | - | - | ✓ | 文件名 |
| `file_path` | ✓ | ✓ | ✗ | ✗ | ✓ | 文件相对路径（SVG/插画可空） |
| `file_size` | ✓ | ✓ | - | - | ✓ | 文件大小 |
| `mime_type` | ✓ | ✓ | - | - | ✓ | MIME类型 |
| `thumbnail_path` | ✓ | ✓ | ✓ | ✓ | ✓ | 缩略图路径 |
| `width` | - | - | ✓ | ✓ | ✓ | 资源宽度 |
| `height` | - | - | ✓ | ✓ | ✓ | 资源高度 |
| `description` | ✓ | ✓ | ✓ | ✓ | ✓ | 描述文本 |
| `raw_data` | ✓ | - | ✓ | ✓ | - | 原始JSON数据 |
| `created_by` | ✓ | ✓ | ✓ | ✓ | ✓ | 创建者 |

**符号说明：**
- ✓ = 必填或有值
- ✗ = 可空（字段存在，值可为NULL）
- - = 不使用或不适用

### 5.2 file_path 字段使用说明

#### 字段语义

- `file_path` 存储资源的文件相对路径（相对于 FILE_ROOT_DIR）
- 前端可通过 `/static/{file_path}` 访问实际文件
- `file_path` 可为 NULL，表示该资源无本地存储的文件

#### 各资源类型的 file_path 使用情况

| 类型 | file_path | 说明 |
|------|-----------|------|
| 组件集 | ✅ 必有 | 存储 hex 文件路径，用于 DSL 实例化 |
| 模版 | ✅ 必有 | 存储 hex 文件路径，用于 DSL 应用 |
| SVG图标 | ❌ 可空 | 仅存储元数据，SVG 文件可能在外部系统管理 |
| 插画 | ❌ 可空 | 仅存储元数据，插画文件可能在外部系统管理 |
| 图片 | ✅ 必有 | 存储图片文件路径，用于缩略图和原图展示 |

#### 设计理念

- **有文件需求的资源**（组件、模版、图片）→ `file_path` 必须存储
- **纯元数据检索的资源**（SVG图标、插画）→ `file_path` 可为空
- 前端应根据 `resource_type` + `file_path` 判断是否可访问静态文件

### 5.3 详情表字段（按类型）

**组件（resource_type=1）：**
- 使用 `component_variants` 表
- 关键字段：`lib_file_key`, `lib_name`, `canvas_name`, `component_name`

**SVG图标（resource_type=3）：**
- 使用 `resource_icons` 表
- 关键字段：`chinese_name`, `english_name`, `category`

**插画（resource_type=4）：**
- 使用 `resource_illus` 表
- 关键字段：`category`, `tags`, `version`

---

## 六、数据流程说明

### 6.1 组件集入库流程

```
读取 component_map.json
  └─ 提取 lib_file_key 和 lib_name
    ↓
读取 component_index.json
  └─ 提取 canvas_name, component_name 等组件集信息
    ↓
遍历所有变体（variants）
  └─ 写 resources 主表（通用字段）
  └─ 写 component_variants 详情表（包含 lib_file_key, lib_name）
    ↓
入向量库（metadata 包含 lib_name）
```

### 6.2 SVG/插画入库流程

```
读取 icons.json / illus.json
  └─ 提取 icon_id, chinese_name, english_name 等
    ↓
写 resources 主表（通用字段）
  └─ 写 resource_icons / resource_illus 详情表
    ↓
入向量库（metadata 包含分类、标签等）
```

---

## 七、修改历史

| 日期 | 修改内容 | 影响表 |
|------|---------|--------|
| 2026-07-08 | 新增 `lib_file_key`, `lib_name` 字段 | component_variants |
| 2026-07-08 | 删除 `domain` 字段 | component_variants |
| 2026-07-08 | 删除 `sort_order` 字段 | resources |
| 2026-07-08 | 补充 `file_path` 字段使用说明 | 文档更新 |

---

## 八、ORM 定义位置

所有表结构定义位于：`app/models/resource.py`

**对应关系：**
- `Resource` 类 → `resources` 表
- `ResourceTag` 类 → `resource_tags` 表
- `ComponentVariant` 类 → `component_variants` 表
- `ResourceIcon` 类 → `resource_icons` 表
- `ResourceIllus` 类 → `resource_illus` 表