# 向量库集成说明

本文档描述设计资源库管理系统与向量服务的集成方式，覆盖**初始化入库、数据查询、数据更新**三个阶段。

当前支持入向量库的资源类型：组件集（type=1）、SVG 图标（type=3）。

---

## 一、初始化阶段

### 数据来源

| 资源类型 | 原始文件 |
|---------|---------|
| 组件集 | `storage/component/component_map.json` → 各 `component_index.json` |
| SVG 图标 | `storage/icon/icons.json` |
| 变体属性翻译 | `storage/component/value_translations.json` |

`component_map.json` 记录所有组件库的索引文件路径，每个 `component_index.json` 包含该组件库下所有组件集及其变体数据。`value_translations.json` 用于将变体属性的英文值（如 `normal`、`disabled`）翻译为中文，供构建 Embedding 文本使用。

### 存在哪

**关系型数据库**（SQLite / MySQL）

| 表 | 写入内容 |
|----|---------|
| `resources` | 每条变体 / 每个图标对应一条主记录，存基础信息和原始 JSON |
| `component_variants` | 组件变体结构化字段：`domain`、`canvas_name`、`component_name`、`variant_key` 等 |
| `resource_icons` | 图标结构化字段：`english_name`、`category` |

DB 写入以 `(name, resource_type)` 为幂等键，重复调用不会产生重复记录。

**向量库**（通过向量服务 `http://localhost:8000`）

| 资源类型 | 向量 type | data_id |
|---------|----------|---------|
| 组件集变体 | `component` | `resources.id`（字符串） |
| SVG 图标 | `icon` | `resources.id`（字符串） |

### Embedding 文本构建规则

**组件变体**

```
{component_name} {canvas_name去数字前缀} {变体属性翻译}
```

变体属性（如 `size=normal, disabled=false`）按逗号拆分，每个 `value` 查 `value_translations.json` 得到中文，拼为 `{英文} {中文}`：

```
示例：文字链接 基础类 normal 标准 false 可用 independent 独立
```

**SVG 图标**

```
{name} {处理后的 english_name} {处理后的 description} {category}
```

- `english_name`：含下划线时视为标识符，去 `ic_` 前缀后下划线转空格；否则直接使用
- `description`：含中文直接使用；纯英文 camelCase 按大写拆词

### 存完之后做什么

1. DB 全部写入并 `commit` 后，收集本次所有条目的 `data_id`、`text`、`metadata`
2. 按每批 100 条，调向量服务 `POST /api/v1/ingest` 批量入库
3. 向量服务以 `data_id` 为幂等键覆盖写入，重复调用安全
4. 向量入库失败只记 `WARNING` 日志，**不回滚 DB**，保证主数据不受影响

> **开关控制**：`.env` 中 `VECTOR_SERVICE_ENABLED=false`（默认）时跳过向量入库步骤，仅写 DB。向量服务就绪后改为 `true` 即可。

### 触发接口

| 接口 | 说明 |
|------|------|
| `POST /api/init` | 全量初始化（组件 + 图标 + 插画 + 模版） |
| `POST /api/init/component` | 仅初始化组件集 |
| `POST /api/init/icon` | 仅初始化 SVG 图标 + 插画（仅 SVG 进向量库） |

---

## 二、数据查询

系统提供两条查询路径，适用于不同场景。

### 路径 A：语义搜索（向量检索）

适用于自然语言描述的模糊查询，如"蓝色主按钮"、"导航类图标"。

**数据流：**

```
调用方
  → POST /api/vector/search
  → 向量服务 POST /api/v1/search
  → 返回按相似度排序的 data_id 列表
  → 以 data_id（即 resource_id）批量查 DB
  → 合并向量得分 + DB 完整资源信息
  → 返回调用方
```

**请求参数：**

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `type` | `component` 或 `icon` | 必填 |
| `query` | 自然语言搜索词 | 必填 |
| `mode` | `vector`（语义）/ `text`（关键词）/ `hybrid`（混合） | `hybrid` |
| `top_k` | 返回条数 | `10` |
| `filters` | metadata 字段过滤，如 `{"metadata.domain": "ICT_UI"}` | 无 |
| `hybrid_weight` | hybrid 模式下向量分数权重（0~1） | `0.7` |

**响应结构：**

```json
{
  "results": [
    {
      "data_id": "42",
      "score": 0.92,
      "text": "主按钮 基础类 normal 标准",
      "metadata": { "component_name": "主按钮", "domain": "ICT_UI", ... },
      "resource": {
        "id": 42,
        "name": "主按钮 / size=normal, disabled=false",
        "resource_type": 1,
        "description": null,
        "file_path": "component/be1d....txt",
        "thumbnail_path": null
      }
    }
  ]
}
```

### 路径 B：结构化列表查询

适用于按类型、分类等条件的精确过滤，如"查看所有 navigation 分类图标"。

**数据流：**

```
调用方
  → GET /api/resources?resource_type=3&...
  → 直接查 DB
  → 返回调用方
```

使用现有 `/api/resources`、`/api/resources/categories` 等接口，不经过向量服务。

---

## 三、数据更新

### 触发时机

重新执行初始化接口（`/api/init/component` 或 `/api/init/icon`）即可触发更新，接口幂等，可反复调用。

### 数据来源

同初始化阶段，重新读取 `storage/` 下对应的 JSON 文件。若源文件内容有变化，更新后的数据会覆盖 DB 和向量库中的旧记录。

### 更新逻辑

**DB 更新**

以 `(name, resource_type)` 为幂等键执行 upsert：
- 记录不存在 → 新增
- 记录已存在 → 覆盖更新所有字段（包括 `domain`、`canvas_name` 等结构化字段）

**向量库更新**

ingest 接口以 `data_id` 为覆盖键：
- `data_id` 不存在 → 新增
- `data_id` 已存在 → 覆盖，若 `text` 有变化则重新生成向量

由于 `data_id = resources.id`，只要 DB 记录的主键稳定，向量库与 DB 始终保持一致。

### 单条更新（扩展）

向量服务提供 `PUT /api/v1/update` 接口支持单条更新，当前系统暂未封装对外接口，如需支持单条资源的向量更新，可在 `vector_router.py` 中扩展。

---

## 附：服务依赖关系

```
调用方
  ├─ POST /api/init/*         写 DB + 批量入向量库
  └─ POST /api/vector/search  语义搜索

当前服务（:8009）
  ├─ 读写 DB（SQLite / MySQL）
  └─ 调向量服务（:8000）
       └─ 调文本向量化服务（:8099，TextToVec）
```

| 服务 | 地址 | 说明 |
|------|------|------|
| 当前系统 | `:8009` | 资源库管理服务 |
| 向量服务 | `:8000`（`VECTOR_SERVICE_URL`） | 管理向量存储与检索 |
| TextToVec | `:8099` | 文本转向量，向量服务内部调用 |
