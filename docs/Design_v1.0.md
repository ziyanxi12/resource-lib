# 资源库设计方案 v1.0

> 设计目标：实现数据与业务分离，支持所有类型资源的统一入库与向量检索

---

## 一、设计理念

### 核心原则

1. **数据与业务分离**：资源数据存储与业务逻辑解耦
2. **统一入库模板**：所有类型资源使用同一套字段结构
3. **向量智能检索**：基于向量相似度的资源搜索
4. **层级分类管理**：类型-来源-分组-具体数据的层级结构

### 层级结构

```
类型（resource_type）
    ↓
来源（source_id）
    ↓
分组（group_id）
    ↓
具体数据（resources）
```

---

## 二、数据库字段设计

### resources 主表字段清单（共21个字段）

| 序号 | 字段 | 类型 | 必填 | 说明 | 分类 |
|------|------|------|------|------|------|
| **必备字段** |
| 1 | `name` | VARCHAR(255) | ✓ | 资源名称（允许重复） | 必备 |
| 2 | `description` | TEXT | | 资源描述 | 必备 |
| 3 | `tags` | - | | 标签（子表 resource_tags 存储） | 必备 |
| **层级关系字段** |
| 4 | `resource_type` | SMALLINT | ✓ | 资源类型（1-6） | 层级 |
| 5 | `source_id` | INT | ✓ | 来源ID | 层级 |
| 6 | `group_id` | INT | | 分组ID | 层级 |
| **文件相关字段** |
| 7 | `file_name` | VARCHAR(255) | | 实体文件名 | 文件 |
| 8 | `file_url` | VARCHAR(500) | | 文件链接（外部） | 文件 |
| 9 | `file_path` | VARCHAR(500) | | 文件路径（本地） | 文件 |
| 10 | `file_size` | INT | | 文件大小（bytes） | 文件 |
| 11 | `file_type` | VARCHAR(50) | | 文件类型 | 文件 |
| 12 | `width` | FLOAT | | 实体宽度（px） | 文件 |
| 13 | `height` | FLOAT | | 实体高度（px） | 文件 |
| 14 | `thumbnail_path` | VARCHAR(500) | | 缩略图路径 | 文件 |
| **业务数据字段** |
| 15 | `search_text` | TEXT | | 业务搜索关键词 | 业务 |
| 16 | `vector_text` | TEXT | | 向量文本（四个字段拼接，存储） | 业务 |
| **原始数据字段** |
| 17 | `raw_data` | JSON | | 原始数据 JSON | 原始 |
| **时间字段** |
| 18 | `created_at` | DATETIME | ✓ | 创建时间 | 时间 |
| 19 | `updated_at` | DATETIME | ✓ | 更新时间 | 时间 |
| 20 | `data_updated_at` | DATETIME | | 数据库更新时间（向量同步判断） | 时间 |
| 21 | `vector_updated_at` | DATETIME | | 向量库更新时间 | 时间 |

### 字段使用说明

#### 必填字段

- **name**：资源名称，唯一必填字段，允许重复
- **resource_type**：资源类型编号（1-6）
- **source_id**：来源ID，关联 resource_sources 表
- **created_at / updated_at**：时间戳，自动维护

#### 可选字段

- 所有其他字段均可为空，根据资源类型按需填充

#### 文件字段说明

- `file_url`：外部文件链接（如 CDN）
- `file_path`：本地文件相对路径（相对于 FILE_ROOT_DIR）
- 两者可同时存在，或只存在其一

#### 层级字段说明

- `resource_type`：资源类型（1=组件 2=模版 3=SVG 4=插画 5=图片 6=文件）
- `source_id`：数据来源（Figma、手工上传、API同步等）
- `group_id`：分组ID，支持树形分组结构

---

## 三、关联表设计

### resource_tags（标签表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK | 主键 |
| `resource_id` | INT | FK | 外键→resources.id，级联删除 |
| `tag` | VARCHAR(100) | NOT NULL | 标签内容 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

**说明：**
- 一个资源可以有多个标签（1:N 关系）
- 删除资源时自动删除关联标签（CASCADE）

### resource_sources（来源表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK | 主键 |
| `code` | VARCHAR(50) | UNIQUE | 来源代码（figma, manual, api_sync） |
| `name` | VARCHAR(255) | NOT NULL | 来源名称 |
| `resource_type` | SMALLINT | NOT NULL | 关联资源类型 |
| `is_sync_source` | TINYINT | DEFAULT 0 | 是否同步来源 |
| `config` | JSON | | 来源配置（API 地址、认证信息等） |
| `is_active` | TINYINT | DEFAULT 1 | 是否启用 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

### resource_groups（分组表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK | 主键 |
| `resource_type` | SMALLINT | NOT NULL | 资源类型 |
| `source_id` | INT | FK, NOT NULL | 来源ID（分组按来源独立） |
| `name` | VARCHAR(255) | NOT NULL | 分组名称 |
| `parent_id` | INT | FK | 父分组ID |
| `level` | SMALLINT | DEFAULT 0 | 层级深度（0=根节点） |
| `real_path` | VARCHAR(500) | NOT NULL | 完整路径（根分组/一级/二级） |
| `sort_order` | INT | DEFAULT 0 | 排序序号 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

**说明：**
- 分组按来源独立：每个来源有独立的分组树
- 支持树形结构：通过 parent_id 和 level 维护层级关系

---

## 四、向量文本构建逻辑

### 1. 四个字段拼接规则

```
向量文本 = name + description + tags + search_text
```

**字段来源：**
- `name`：资源名称（主表，必填）
- `description`：资源描述（主表，可空）
- `tags`：标签（子表 resource_tags 关联查询，可空）
- `search_text`：业务搜索关键词（主表，可空）

### 2. 实现逻辑

```python
def build_vector_text(resource: Resource) -> str:
    """
    构造向量文本：name + description + tags + search_text
    """
    # 1. 查询 tags（从子表关联）
    tags_list = db.query(ResourceTag.tag).filter(
        ResourceTag.resource_id == resource.id
    ).all()
    tags_str = ' '.join([t[0] for t in tags_list])
    
    # 2. 四个字段拼接
    parts = [
        resource.name or '',                    # 字段1：名称（必填）
        resource.description or '',             # 字段2：描述（可空）
        tags_str,                               # 字段3：标签（子表）
        resource.search_text or ''              # 字段4：业务关键词（可空）
    ]
    
    # 3. 拼接并清理多余空格
    vector_text = ' '.join(filter(None, parts))
    return ' '.join(vector_text.split())

# 入库时存储到 vector_text 字段
resource.vector_text = build_vector_text(resource)
db.commit()
```

### 3. 关键特性

- **存储到主表**：vector_text 字段存储拼接后的向量文本
- **实时同步**：字段更新时同步更新 vector_text
- **空值处理**：过滤空字段，避免多余空格
- **便于查询**：可直接查看向量文本内容，便于调试

---

## 五、向量库设计

### 1. 索引结构（按类型分索引）

**索引名称格式：**
```
{VECTOR_INDEX_PREFIX}_{type_name}
```

**配置方式：**
- 环境变量：`VECTOR_INDEX_PREFIX`
- 默认值：`lib_resource`

**索引列表：**
- `{prefix}_component`      # resource_type=1（组件）
- `{prefix}_template`       # resource_type=2（模版）
- `{prefix}_icon`           # resource_type=3（SVG）
- `{prefix}_illustration`   # resource_type=4（插画）
- `{prefix}_image`          # resource_type=5（图片）
- `{prefix}_file`           # resource_type=6（文件）

**示例（VECTOR_INDEX_PREFIX=lib_resource）：**
- `lib_resource_component`
- `lib_resource_template`
- `lib_resource_icon`
- `lib_resource_illustration`
- `lib_resource_image`
- `lib_resource_file`

### 2. 文档结构

```json
{
  "id": 1001,
  "text": "主按钮 主要操作按钮，用于页面核心操作 表单 确认 按钮",
  "metadata": {
    "source_id": 1,
    "group_id": 10
  }
}
```

**字段说明：**
- `id`：数据库唯一ID（resources.id）
- `text`：向量文本（四个字段拼接，存储在 vector_text 字段）
- `metadata`：元数据（用于筛选，不含 resource_type）

### 3. 架构说明

- **不直接连接 ES**：向量库通过中间层（向量管理层）访问
- **向量管理层职责**：索引管理、推送、查询、同步控制等
- **推送流程**：resource.vector_text → 向量管理层 → 向量库

---

## 六、入库流程

### 1. 流程图

```
接收数据
    ↓
必填字段校验（name, resource_type, source_id）
    ↓
创建资源记录（每次新增，不幂等）
    ↓
写入标签（如有，写入 resource_tags 子表）
    ↓
构造向量文本（四个字段拼接）
    ↓
存储向量文本到 vector_text 字段
    ↓
推送到向量库（通过向量管理层）
    ↓
返回资源ID
```

### 2. 幂等性策略

- **全部不幂等**：所有资源每次都新增记录
- **name 允许重复**：不设唯一索引，不判断重复
- **无需 source_data_id**：不依赖来源数据ID做幂等判断

---

## 七、搜索流程

### 1. 搜索接口

**接口定义：**
```
POST /api/resources/search
```

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | String | ✓ | - | 搜索文本 |
| `resource_type` | Int | ✓ | - | 资源类型（1-6） |
| `source_id` | Int | | - | 来源ID（筛选） |
| `group_id` | Int | | - | 分组ID（筛选） |
| `top_k` | Int | | 10 | 返回最相似的 K 条结果（最大50） |
| `response_mode` | String | | `basic` | 响应模式 |

### 2. 三种响应模式

#### basic 模式（LLM 专用）

**返回字段：** `id`, `text`, `score`

**使用场景：** LLM 工具调用、API 集成

```json
{
  "data": [
    {
      "id": 1001,
      "text": "主按钮 主要操作按钮 表单 确认",
      "score": 0.95
    },
    {
      "id": 1002,
      "text": "次按钮 次要操作按钮 表单 取消",
      "score": 0.88
    }
  ]
}
```

#### normal 模式（其他方专用）

**返回字段：** `id`, `text`, `score`, `raw_data`

**使用场景：** 外部系统调用、第三方集成

```json
{
  "data": [
    {
      "id": 1001,
      "text": "主按钮 主要操作按钮 表单 确认",
      "score": 0.95,
      "raw_data": {
        "figma_node_id": "123:456",
        "component_key": "abc123"
      }
    }
  ]
}
```

#### complete 模式（前端专用）

**返回字段：** 全量数据（20+字段）

**使用场景：** 前端表格展示、详情页

```json
{
  "data": [
    {
      "id": 1001,
      "text": "主按钮 主要操作按钮 表单 确认",
      "score": 0.95,
      "name": "主按钮",
      "description": "主要操作按钮，用于页面核心操作",
      "tags": ["表单", "确认"],
      "search_text": "按钮 提交 确认",
      "file_name": "button_primary.hex",
      "file_url": null,
      "file_path": "component/button_primary.hex",
      "file_size": 2048,
      "file_type": "hex",
      "width": null,
      "height": null,
      "thumbnail_path": "thumbnail/button_primary.png",
      "raw_data": {
        "figma_node_id": "123:456",
        "component_key": "abc123"
      },
      "resource_type": 1,
      "source_id": 1,
      "group_id": 10,
      "created_at": "2026-07-14T10:00:00",
      "updated_at": "2026-07-14T10:30:00"
    }
  ]
}
```

### 3. 字段对比表

| 字段 | basic | normal | complete | 说明 |
|------|-------|--------|----------|------|
| `id` | ✓ | ✓ | ✓ | 资源ID |
| `text` | ✓ | ✓ | ✓ | 向量文本 |
| `score` | ✓ | ✓ | ✓ | 相似度分数 |
| `raw_data` | - | ✓ | ✓ | 原始数据 |
| `name` | - | - | ✓ | 资源名称 |
| `description` | - | - | ✓ | 描述 |
| `tags` | - | - | ✓ | 标签 |
| `file_*` | - | - | ✓ | 文件相关字段 |
| `*` | - | - | ✓ | 其他全量字段 |

### 4. 搜索流程

```
用户输入搜索文本
    ↓
文本向量化（通过向量管理层）
    ↓
向量相似度搜索（topK 模式）
    ↓
返回最相似的 K 条结果（按 score 降序）
    ↓
根据 response_mode 构造返回数据
    ↓
返回搜索结果
```

### 5. 使用示例

#### LLM 调用（获取最相似的10条）
```json
{
  "text": "按钮",
  "resource_type": 1,
  "response_mode": "basic"
}
```

#### 外部系统调用（获取最相似的20条）
```json
{
  "text": "按钮",
  "resource_type": 1,
  "top_k": 20,
  "response_mode": "normal"
}
```

#### 前端调用（获取最相似的50条全量数据）
```json
{
  "text": "按钮",
  "resource_type": 1,
  "source_id": 1,
  "top_k": 50,
  "response_mode": "complete"
}
```

### 6. 关键设计决策

| 决策项 | 设计 |
|--------|------|
| **搜索模式** | 纯 topK，不分页 |
| **top_k 默认值** | 10 |
| **top_k 上限** | 50 |
| **返回总数** | 不返回 total |
| **排序方式** | 按相似度 score 降序 |
```

---

## 八、数据库索引

### 主表索引

```sql
-- 查询索引
INDEX idx_type_source (resource_type, source_id)
INDEX idx_group (group_id)

-- 同步控制索引
INDEX idx_data_updated (data_updated_at)
INDEX idx_vector_updated (vector_updated_at)

-- 不需要幂等索引（全部不幂等）
-- 不需要 name 唯一索引（允许重复）
```

### 子表索引

```sql
-- resource_tags
INDEX idx_resource_id (resource_id)
INDEX idx_tag (tag)

-- resource_sources
UNIQUE INDEX idx_code (code)

-- resource_groups
INDEX idx_type_source (resource_type, source_id)
INDEX idx_parent (parent_id)
UNIQUE INDEX idx_name_type_source (name, resource_type, source_id)
```

---

## 九、数据示例

### 示例1：组件资源（resource_type=1）

```json
{
  "name": "主按钮",
  "description": "主要操作按钮，用于页面核心操作",
  "resource_type": 1,
  "source_id": 1,
  "group_id": 10,
  "tags": ["表单", "确认", "基础"],
  "search_text": "按钮 提交 确认 基础组件",
  "file_name": "button_primary.hex",
  "file_url": null,
  "file_path": "component/button_primary.hex",
  "file_size": 2048,
  "file_type": "hex",
  "width": null,
  "height": null,
  "thumbnail_path": "thumbnail/button_primary.png",
  "raw_data": {
    "figma_node_id": "123:456",
    "component_key": "abc123",
    "canvas_name": "1.基础类"
  }
}
```

**向量文本：**
```
"主按钮 主要操作按钮，用于页面核心操作 表单 确认 基础 按钮 提交 确认 基础组件"
```

### 示例2：SVG 图标（resource_type=3）

```json
{
  "name": "首页图标",
  "description": "首页导航图标，用于导航栏",
  "resource_type": 3,
  "source_id": 3,
  "group_id": 30,
  "tags": ["导航", "系统"],
  "search_text": "home 导航 首页",
  "file_name": "home.svg",
  "file_url": "https://cdn.example.com/icons/home.svg",
  "file_path": null,
  "file_size": 1024,
  "file_type": "svg",
  "width": 24,
  "height": 24,
  "thumbnail_path": "thumbnail/home.png",
  "raw_data": {
    "icon_id": "100",
    "english_name": "home",
    "category": "navigation"
  }
}
```

**向量文本：**
```
"首页图标 首页导航图标，用于导航栏 导航 系统 home 导航 首页"
```

### 示例3：模版资源（resource_type=2）

```json
{
  "name": "登录页面模版",
  "description": "标准登录页面模版，包含账号密码登录",
  "resource_type": 2,
  "source_id": 2,
  "group_id": 20,
  "tags": ["登录", "认证"],
  "search_text": "登录 认证 表单",
  "file_name": "login_template.hex",
  "file_url": null,
  "file_path": "template/login.hex",
  "file_size": 4096,
  "file_type": "hex",
  "width": 1920,
  "height": 1080,
  "thumbnail_path": "thumbnail/login.png",
  "raw_data": {
    "version": "1.0",
    "author": "设计团队"
  }
}
```

---

## 十、API 接口设计

### 资源管理接口

```
POST   /api/resources                    # 创建资源（不幂等）
PUT    /api/resources/{id}               # 更新资源
DELETE /api/resources/{id}               # 删除资源（软删除）
GET    /api/resources/{id}               # 获取资源详情
GET    /api/resources                    # 资源列表（支持筛选）
POST   /api/resources/search             # 向量搜索
POST   /api/resources/batch              # 批量创建
```

### 来源管理接口

```
POST   /api/sources                      # 创建来源
GET    /api/sources                      # 来源列表
PUT    /api/sources/{id}                 # 更新来源
DELETE /api/sources/{id}                 # 删除来源
```

### 分组管理接口

```
POST   /api/groups                       # 创建分组
GET    /api/groups                       # 分组树（按类型+来源）
PUT    /api/groups/{id}                  # 更新分组
DELETE /api/groups/{id}                  # 删除分组
```

---

## 十一、实施清单

### Phase 1: 数据库迁移

- [ ] 创建 `resource_sources` 表
- [ ] 调整 `resources` 表结构（新增字段）
- [ ] 调整 `resource_groups` 表结构（新增 source_id）
- [ ] 迁移现有数据
- [ ] 更新索引

### Phase 2: 后端重构

- [ ] 更新 ORM 模型（`models/resource.py`）
- [ ] 新增 `Source` 模型
- [ ] 实现向量文本构建逻辑
- [ ] 实现向量库推送逻辑
- [ ] 实现搜索接口
- [ ] 更新 API 路由

### Phase 3: 前端改造

- [ ] 新增来源筛选组件
- [ ] 调整分组树加载逻辑（按来源）
- [ ] 新增搜索页面
- [ ] 调整资源列表筛选

### Phase 4: 测试与上线

- [ ] 单元测试
- [ ] 集成测试
- [ ] 数据验证
- [ ] 灰度发布

---

## 十二、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0 | 2026-07-14 | 初始版本，完成核心设计 |
| v1.1 | 2026-07-14 | 新增 vector_text 字段，调整向量文本存储策略；索引名称改为可配置前缀；删除 ES 实现代码，增加向量管理层说明 |
| v1.2 | 2026-07-14 | 搜索接口改为 topK 模式；增加三种响应模式（basic/normal/complete）；删除分页参数，改为 top_k 参数 |