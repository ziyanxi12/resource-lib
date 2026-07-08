# 前端数据展示文档

## 一、五类数据概览

| 资源类型 | resource_type值 | 列表组件 | 详情组件 | 共用情况 |
|---------|----------------|---------|---------|---------|
| **组件** | 1 | `ComponentList.tsx` | `ComponentDetail` | 独立 |
| **模版** | 2 | `ResourceList.tsx` | `ResourceDetail` | 与图片共用 |
| **SVG图标** | 3 | `IconList.tsx` | `IconDetail` | 独立 |
| **插画** | 4 | `IllusList.tsx` | `IllusDetail` | 独立 |
| **图片** | 5 | `ResourceList.tsx` | `ResourceDetail` | 与模版共用 |

---

## 二、数据表展示页

### 1. 组件 (`ComponentList.tsx:192-225`)

| 字段 | 中文表述 | 宽度 | 数据来源 |
|------|---------|------|---------|
| `id` | ID | 68px | `Resource.id` |
| `cv_lib_name` | 组件库 | 120px | `ComponentVariant.lib_name` |
| `cv_canvas_name` | 组件类别 | 120px | `ComponentVariant.canvas_name` |
| `cv_component_name` | 组件名 | 150px | `ComponentVariant.component_name` |
| `cv_variant_name` | 变体名 | 自适应 | `ComponentVariant.name` |
| `tags` | 标签 | 160px | `Resource.tags` |

**向量搜索时额外显示：**
- `score` → "相似度" (88px，百分比显示)

---

### 2. 模版 & 图片 (`ResourceList.tsx:166-190`)

共用同一组件，通过 `type` 参数区分。

| 字段 | 中文表述 | 宽度 | 数据来源 |
|------|---------|------|---------|
| `id` | ID | 72px | `Resource.id` |
| `name` | 名称 | 自适应 | `Resource.name` |
| `description` | 描述 | 自适应 | `Resource.description` |
| `tags` | 标签 | 200px | `Resource.tags` |

---

### 3. SVG图标 (`IconList.tsx:201-241`)

| 字段 | 中文表述 | 宽度 | 数据来源 |
|------|---------|------|---------|
| `id` | ID | 68px | `Resource.id` |
| `icon_id` | 图标ID | 80px | `ResourceIcon.icon_id` |
| `name` / `icon_chinese_name` | 中文名 | 120px | `Resource.name` 或 `ResourceIcon.chinese_name` |
| `icon_english_name` | 英文名 | 140px | `ResourceIcon.english_name` |
| `icon_category` | 分类 | 110px | `ResourceIcon.category` |
| `description` | 描述 | 自适应 | `Resource.description` |
| `tags` | 标签 | 160px | `Resource.tags` |

**向量搜索时额外显示：**
- `score` → "相似度" (88px)

---

### 4. 插画 (`IllusList.tsx:193-231`)

| 字段 | 中文表述 | 宽度 | 数据来源 |
|------|---------|------|---------|
| `id` | ID | 68px | `Resource.id` |
| `illus_id` | 插画ID | 110px | `ResourceIllus.illus_id` |
| `name` | 名称 | 130px | `Resource.name` |
| `illus_category` | 分类 | 110px | `ResourceIllus.category` |
| `illus_tags` | 标签 | 160px | `ResourceIllus.tags` |
| `illus_version` | 版本 | 80px | `ResourceIllus.version` |
| `description` | 描述 | 自适应 | `Resource.description` |

**向量搜索时额外显示：**
- `score` → "相似度" (88px)

---

## 三、详情侧边栏

所有详情组件位于各列表文件内，命名规范：`XXXDetail` 函数。

### 通用结构

每个详情侧边栏包含三个区块：

```
┌─────────────────────────────┐
│  基础信息 (SectionHeader)     │
│  - 通用字段                   │
│  - 类型特定字段               │
├─────────────────────────────┤
│  向量库映射 (SectionHeader)   │
│  - 用于向量检索的字段         │
├─────────────────────────────┤
│  原始JSON (SectionHeader)    │
│  - raw_data 格式化展示        │
└─────────────────────────────┘
```

---

### 1. 组件详情 (`ComponentList.tsx:56-117`)

**基础信息区 (70-97行)**

| 字段 | 中文表述 | 数据来源 |
|------|---------|---------|
| `id` | ID | `Resource.id` |
| `name` | 名称 | `Resource.name` |
| `description` | 描述 | `Resource.description` |
| `tags` | 标签 | `Resource.tags` |
| `created_at` | 创建时间 | `Resource.created_at` |
| `updated_at` | 更新时间 | `Resource.updated_at` |
| `file_name` | 文件名 | `Resource.file_name` |
| `file_path` | 文件路径 | `Resource.file_path` |
| `thumbnail_path` | 缩略图路径 | `Resource.thumbnail_path` |
| `mime_type` | 文件类型 | `Resource.mime_type` |
| `file_size` | 文件大小 | `Resource.file_size` |
| `dimensions` | 资源尺寸 | `Resource.dimensions` |
| `cv_lib_name` | 组件库 | `ComponentVariant.lib_name` |
| `cv_canvas_name` | 组件类别 | `ComponentVariant.canvas_name` |
| `cv_component_name` | 组件名 | `ComponentVariant.component_name` |
| `cv_component_guid` | 组件 GUID | `ComponentVariant.component_guid` |
| `cv_component_key` | 组件 Key | `ComponentVariant.component_key` |
| `cv_variant_name` | 变体名 | `ComponentVariant.name` |
| `cv_variant_guid` | 变体 GUID | `ComponentVariant.guid` |
| `cv_variant_key` | 变体 Key | `ComponentVariant.variant_key` |
| `cv_component_props` | 变体属性 | `ComponentVariant.component_props` |

**向量库映射区 (100-105行)**

| 字段 | 中文表述 |
|------|---------|
| `vector_text` | 向量文本 |
| `cv_component_name` | 组件名 |
| `cv_canvas_name` | 组件类别 |
| `cv_variant_name` | 变体名 |
| `cv_lib_name` | 组件库 |

---

### 2. 模版 & 图片详情 (`ResourceList.tsx:55-101`)

**基础信息区 (69-83行)**

| 字段 | 中文表述 | 数据来源 |
|------|---------|---------|
| `id` | ID | `Resource.id` |
| `name` | 名称 | `Resource.name` |
| `description` | 描述 | `Resource.description` |
| `tags` | 标签 | `Resource.tags` |
| `created_at` | 创建时间 | `Resource.created_at` |
| `updated_at` | 更新时间 | `Resource.updated_at` |
| `file_name` | 文件名 | `Resource.file_name` |
| `file_path` | 文件路径 | `Resource.file_path` |
| `thumbnail_path` | 缩略图路径 | `Resource.thumbnail_path` |
| `mime_type` | 文件类型 | `Resource.mime_type` |
| `file_size` | 文件大小 | `Resource.file_size` |
| `dimensions` | 资源尺寸 | `Resource.dimensions` |

**向量库映射区 (86-90行)**

| 字段 | 中文表述 |
|------|---------|
| `vector_text` | 向量文本 |
| `name` | 名称 |
| `description` | 描述 |

---

### 3. SVG图标详情 (`IconList.tsx:54-110`)

**基础信息区 (69-88行)**

| 字段 | 中文表述 | 数据来源 |
|------|---------|---------|
| 通用字段 | 同模版 | `Resource.*` |
| `icon_id` | 图标ID | `ResourceIcon.icon_id` |
| `icon_chinese_name` | 中文名 | `ResourceIcon.chinese_name` |
| `icon_name` | 英文全称 | `ResourceIcon.name` |
| `icon_english_name` | 英文名 | `ResourceIcon.english_name` |
| `icon_category` | 分类 | `ResourceIcon.category` |

**向量库映射区 (91-97行)**

| 字段 | 中文表述 |
|------|---------|
| `vector_text` | 向量文本 |
| `icon_category` | 分类 |
| `icon_chinese_name` | 中文名 |
| `icon_name` | 英文全称 |
| `icon_english_name` | 英文名 |
| `description` | 描述 |

---

### 4. 插画详情 (`IllusList.tsx:52-104`)

**基础信息区 (67-85行)**

| 字段 | 中文表述 | 数据来源 |
|------|---------|---------|
| 通用字段 | 同模版 | `Resource.*` |
| `illus_id` | 插画ID | `ResourceIllus.illus_id` |
| `illus_category` | 分类 | `ResourceIllus.category` |
| `illus_tags` | 插画标签 | `ResourceIllus.tags` |
| `illus_version` | 版本 | `ResourceIllus.version` |

**向量库映射区 (88-92行)**

| 字段 | 中文表述 |
|------|---------|
| `vector_text` | 向量文本 |
| `illus_category` | 分类 |
| `name` | 名称 |
| `description` | 描述 |

---

## 四、字段命名映射规范

### 前端字段 → 后端ORM映射

#### 通用字段（所有类型）

| 前端字段 | ORM表 | ORM字段 |
|---------|--------|---------|
| `id` | `resources` | `id` |
| `name` | `resources` | `name` |
| `description` | `resources` | `description` |
| `tags` | `resource_tags` | `tag` (列表) |
| `file_name` | `resources` | `file_name` |
| `file_path` | `resources` | `file_path` |
| `file_size` | `resources` | `file_size` |
| `mime_type` | `resources` | `mime_type` |
| `thumbnail_path` | `resources` | `thumbnail_path` |
| `dimensions` | `resources` | `dimensions` |
| `raw_data` | `resources` | `raw_data` |
| `created_at` | `resources` | `created_at` |
| `updated_at` | `resources` | `updated_at` |
| `vector_text` | `resources` | `vector_text` |

#### 组件专用字段（cv_*）

| 前端字段 | ORM表 | ORM字段 |
|---------|--------|---------|
| `cv_lib_file_key` | `component_variants` | `lib_file_key` |
| `cv_lib_name` | `component_variants` | `lib_name` |
| `cv_canvas_name` | `component_variants` | `canvas_name` |
| `cv_component_name` | `component_variants` | `component_name` |
| `cv_component_guid` | `component_variants` | `component_guid` |
| `cv_component_key` | `component_variants` | `component_key` |
| `cv_variant_name` | `component_variants` | `name` |
| `cv_variant_guid` | `component_variants` | `guid` |
| `cv_variant_key` | `component_variants` | `variant_key` |
| `cv_component_props` | `component_variants` | `component_props` |

#### 图标专用字段（icon_*）

| 前端字段 | ORM表 | ORM字段 |
|---------|--------|---------|
| `icon_id` | `resource_icons` | `icon_id` |
| `icon_chinese_name` | `resource_icons` | `chinese_name` |
| `icon_name` | `resource_icons` | `name` |
| `icon_english_name` | `resource_icons` | `english_name` |
| `icon_category` | `resource_icons` | `category` |

#### 插画专用字段（illus_*）

| 前端字段 | ORM表 | ORM字段 |
|---------|--------|---------|
| `illus_id` | `resource_illus` | `illus_id` |
| `illus_category` | `resource_illus` | `category` |
| `illus_tags` | `resource_illus` | `tags` |
| `illus_version` | `resource_illus` | `version` |

---

## 五、修改指引

### 场景1：修改表格列

**步骤：**
1. 找到对应的列表组件文件（参考第一部分表格）
2. 定位 `baseColumns` 定义区域（行号见第二部分）
3. 修改/新增/删除列定义
4. 如需新字段，确保：
   - 后端已返回该字段
   - 前端 `types.ts` 中 `Resource` 接口已添加字段定义

---

### 场景2：修改详情侧边栏

**步骤：**
1. 找到对应列表组件内的 `XXXDetail` 函数（行号见第三部分）
2. 定位具体区块（基础信息 / 向量库映射 / 原始JSON）
3. 使用 `<Field label="中文表述">{item.字段名}</Field>` 添加字段
4. 如需新字段，确保ORM和类型定义已同步

---

### 场景3：修改JSON展示样式

**位置：**
- `ComponentList.tsx:108-116`
- `ResourceList.tsx:92-100`
- `IconList.tsx:100-108`
- `IllusList.tsx:95-103`

**注意：** 修改JSON展示需同步修改4个文件。

---

### 场景4：修改向量库映射字段

**影响范围：**
- 表格列（向量搜索结果列）
- 详情侧边栏的"向量库映射"区块
- 后端向量文本生成逻辑（需确认）

---

## 六、关键代码位置速查表

| 功能 | 文件 | 关键代码位置 |
|------|------|------------|
| Resource类型定义 | `types.ts` | `1-39行` |
| 组件列表表头 | `ComponentList.tsx` | `193-225行` |
| 组件详情 | `ComponentList.tsx` | `56-117行` |
| 模版/图片列表表头 | `ResourceList.tsx` | `166-190行` |
| 模版/图片详情 | `ResourceList.tsx` | `55-101行` |
| 图标列表表头 | `IconList.tsx` | `201-241行` |
| 图标详情 | `IconList.tsx` | `54-110行` |
| 插画列表表头 | `IllusList.tsx` | `193-231行` |
| 插画详情 | `IllusList.tsx` | `52-104行` |
| JSON展示（所有类型） | 4个List文件 | 见第五部分场景3 |
| SectionHeader组件 | 各List文件内 | `20-30行` |
| Field组件 | 各List文件内 | `32-38行` |
| HashVal组件 | 各List文件内 | `41-52行` |

---

## 七、数据表关联关系

```
resources (主表)
    │
    ├─ 1:N ── resource_tags        resource_id → resources.id
    ├─ 1:1 ── component_variants   resource_id → resources.id (仅组件类型)
    ├─ 1:1 ── resource_icons       resource_id → resources.id (仅SVG类型)
    └─ 1:1 ── resource_illus      resource_id → resources.id (仅插画类型)
```

**关联查询说明：**
- 后端通过 SQLAlchemy 的 `relationship` 自动关联
- 前端接收的 `Resource` 对象已包含所有关联字段（扁平化结构）
- 字段命名采用前缀区分：`cv_*`（组件）、`icon_*`（图标）、`illus_*`（插画）