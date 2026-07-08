# 向量数据构造说明

本文档详细说明五类资源的向量数据构造方式，供 AI 辅助代码修改时参考。

---

## 总览

所有资源的向量数据通过 `app/services/vector_text_builder.py` 统一构造，包含三个核心要素：

| 要素 | 说明 | 用途 |
|------|------|------|
| `text` | 可搜索文本字符串 | 用于语义检索和全文搜索 |
| `metadata` | 元数据字典 | 用于精确过滤和结果展示 |
| `data_id` | 唯一标识符 | 用于向量库去重和更新 |

**统一入库入口**: `ingest_vectors()` 函数（line 212-248）

---

## 五类向量拼接字段速览

| 类型 | 拼接字段公式 | data_id来源 |
|------|-------------|------------|
| component | `{component_name} {canvas_name} {variant属性值} {翻译中文}` | variant_key |
| icon | `{category} {chinese_name} {英文全称} {英文短名} {description}` | icon_id |
| illus | `{illus_id} {alias} {description} {category} {tags空格连接} {version}` | illus_id |
| template | `{name} {description}` | resource.id |
| image | `{name} {description}` | resource.id |

---

## 1. 组件集 (component, type=1)

### 【快速参考】拼接字段

**文本公式**: `{component_name} {canvas_name} {variant属性值} {翻译中文}`

**构造示例**: 
- 输入: component_name="文字链接", canvas_name="1.基础类", variant="size=normal, disabled=false"
- 输出: `"文字链接 基础类 normal 可用 正常 启用"`

**data_id**: `variant_key` (来自 ComponentVariant.variant_key)

---

### 详细说明

#### 数据表关联

```
resources (主表)
  └─ component_variants (1:1 关联，通过 resource_id)
```

**关键字段**:
- `ComponentVariant.variant_key` - 变体唯一标识（用作 data_id）
- `ComponentVariant.component_name` - 组件集名称
- `ComponentVariant.canvas_name` - 画布分组名（如"1.基础类")
- `ComponentVariant.name` - 变体属性字符串（如"size=normal, disabled=false")
- `ComponentVariant.lib_file_key` - 组件库文件key
- `ComponentVariant.lib_name` - 组件库名称

#### 文本构造函数

**函数**: `_build_component_text_fn` (line 86-91) → `build_component_text` (line 38-53)

**字段来源优先级**:
1. `raw` 字典（初始化时携带原始JSON）
2. ORM 关联表 `resource.component_variant`

**构造逻辑**:

```python
def build_component_text(component_name: str, canvas_name: str, variant_name: str) -> str:
    # 1. 去除数字前缀（如 "1.基础类" → "基础类")
    clean_canvas = re.sub(r"^\d+\.", "", canvas_name or "").strip()
    clean_name   = re.sub(r"^\d+\.", "", component_name or "").strip()
    
    # 2. 拼接基础部分
    parts = [clean_name, clean_canvas]
    
    # 3. 解析变体属性字符串（如 "size=normal, disabled=false"）
    for pair in (variant_name or "").split(","):
        pair = pair.strip()
        if "=" not in pair:
            if pair:
                parts.append(pair)
            continue
        _, value = pair.split("=", 1)
        value = value.strip()
        
        # 4. 使用翻译文件查找中文同义词
        zh = translations.get(pair, "") or translations.get(value, "")
        parts.append(f"{value} {zh}" if zh else value)
    
    # 5. 空格连接所有部分
    return " ".join(p for p in parts if p)
```

**翻译文件**: `storage/component/value_translations.json`

格式示例：
```json
{
  "disabled=true":  "禁用 不可用 失效 灰态",
  "disabled=false": "可用 正常 启用",
  "size=small":     "小 小型",
  "size=normal":    "标准 常规"
}
```

#### 元数据构造

**函数**: `_build_component_metadata` (line 94-101)

**字段**:
```json
{
  "name":           "资源名称",
  "canvas_name":    "画布分组名",
  "component_name": "组件集名称",
  "lib_name":       "组件库名称"
}
```

---

## 2. SVG图标 (icon, type=3)

### 【快速参考】拼接字段

**文本公式**: `{category} {chinese_name} {英文全称} {英文短名} {description}`

**构造示例**: 
- 输入: category="navigation", chineseName="首页", name="it_home", englishName="home", description="房子图标"
- 输出: `"navigation 首页 it home home 房子图标，用于导航首页"`

**data_id**: `icon_id` (来自 ResourceIcon.icon_id)

---

### 详细说明

#### 数据表关联

```
resources (主表)
  └─ resource_icons (1:1 关联，通过 resource_id)
```

**关键字段**:
- `ResourceIcon.icon_id` - 图标原始ID（用作 data_id）
- `ResourceIcon.chinese_name` - 中文名称
- `ResourceIcon.name` - 英文全称（如"it_home")
- `ResourceIcon.english_name` - 英文短名（如"home")
- `ResourceIcon.category` - 分类（如"navigation", "system")
- `Resource.description` - 描述文本

#### 文本构造函数

**函数**: `_build_icon_text_fn` (line 104-111) → `build_icon_text` (line 75-83)

**字段来源优先级**:
1. `raw` 字典（初始化时携带 icons.json 原始数据）
2. ORM 关联表 `resource.icon_detail`
3. `resource.name` / `resource.description`

**构造逻辑**:

```python
def build_icon_text(category: str, chinese_name: str, name: str, english_name: str, description: str) -> str:
    parts = [
        category or "",
        chinese_name or "",
        _process_english_name(name),        # 处理英文全称
        _process_english_name(english_name), # 处理英文短名
        _process_description(description),   # 处理描述
    ]
    return " ".join(p for p in parts if p)
```

**辅助函数**:

1. `_process_english_name` (line 56-64):
   - 移除 "ic_" 前缀（如 "ic_home" → "home")
   - 下划线转空格（如 "it_home" → "it home")

2. `_process_description` (line 67-72):
   - 如包含中文，直接返回
   - 英文驼峰命名添加空格（如 "GearIcon" → "Gear Icon")

#### 元数据构造

**函数**: `_build_icon_metadata` (line 114-121)

**字段**:
```json
{
  "name":         "资源名称",
  "description":  "描述文本",
  "english_name": "英文短名",
  "category":     "分类"
}
```

---

## 3. 插画 (illus, type=4)

### 【快速参考】拼接字段

**文本公式**: `{illus_id} {alias} {description} {category} {tags空格连接} {version}`

**构造示例**: 
- 输入: illus_id="EMPLY_ILL", alias="空状态", description="用于列表为空时的占位插画", category="领域A", tags=["空状态illus"], version="2.0"
- 输出: `"EMPLY_ILL 空状态 用于列表为空时的占位插画 领域A 空状态illus 2.0"`

**data_id**: `illus_id` (来自 ResourceIllus.illus_id)

---

### 详细说明

#### 数据表关联

```
resources (主表)
  └─ resource_illus (1:1 关联，通过 resource_id)
```

**关键字段**:
- `ResourceIllus.illus_id` - 插画原始ID（用作 data_id）
- `ResourceIllus.category` - 分类
- `ResourceIllus.tags` - 标签列表（JSON数组）
- `ResourceIllus.version` - 版本号
- `Resource.name` - 别名（alias）
- `Resource.description` - 描述

#### 文本构造函数

**函数**: `_build_illus_text_fn` (line 124-131)

**字段来源优先级**:
1. `raw` 字典（初始化时携带 illus.json 原始数据）
2. ORM 关联表 `resource.illus_detail`

**构造逻辑**:

```python
def _build_illus_text_fn(resource: "Resource", raw: dict) -> str:
    il = resource.illus_detail
    illus_id = raw.get("id") or (il.illus_id if il else "") or ""
    alias    = resource.name or ""
    desc     = resource.description or ""
    category = raw.get("category") or (il.category if il else "") or ""
    tags     = raw.get("tags") or (il.tags if il else []) or []
    tag_str  = " ".join(tags) if isinstance(tags, list) else str(tags)
    version  = raw.get("version") or (il.version if il else "") or ""
    return " ".join(p for p in [illus_id, alias, desc, category, tag_str, version] if p)
```

#### 元数据构造

**函数**: `_build_illus_metadata` (line 134-139)

**字段**:
```json
{
  "name":     "资源名称",
  "category": "分类",
  "version":  "版本号"
}
```

---

## 4. 模版 (template, type=2)

### 【快速参考】拼接字段

**文本公式**: `{name} {description}`

**构造示例**: 
- 输入: name="登录页面模版", description="适用于移动端登录页面"
- 输出: `"登录页面模版 适用于移动端登录页面，包含账号密码输入框和登录按钮"`

**data_id**: `resource.id` (来自 Resource.id)

---

### 详细说明

#### 数据表关联

仅使用 `resources` 主表，无关联表。

**关键字段**:
- `Resource.id` - 主键ID（用作 data_id）
- `Resource.name` - 模版名称
- `Resource.description` - 描述

#### 文本构造函数

**函数**: `_build_simple_text` (line 142-143)

**构造逻辑**:

```python
def _build_simple_text(resource: "Resource", raw: dict) -> str:
    return f"{resource.name} {resource.description or ''}".strip()
```

#### 元数据构造

**函数**: `_build_simple_metadata` (line 146-147)

**字段**:
```json
{
  "name":        "模版名称",
  "description": "描述文本"
}
```

---

## 5. 图片 (image, type=5)

### 【快速参考】拼接字段

**文本公式**: `{name} {description}`

**构造示例**: 
- 输入: name="产品截图.jpg", description="首页展示图"
- 输出: `"产品截图.jpg 首页展示图"`

**data_id**: `resource.id` (来自 Resource.id)

---

### 详细说明

#### 数据表关联

仅使用 `resources` 主表，无关联表。

**关键字段**:
- `Resource.id` - 主键ID（用作 data_id）
- `Resource.name` - 图片名称
- `Resource.description` - 描述（可选）

#### 文本构造函数

**函数**: `_build_simple_text` (line 142-143) - 与模版相同

**构造逻辑**:
```python
def _build_simple_text(resource: "Resource", raw: dict) -> str:
    return f"{resource.name} {resource.description or ''}".strip()
```

#### 元数据构造

**函数**: `_build_simple_metadata` (line 146-147) - 与模版相同

**字段**:
```json
{
  "name":        "图片名称",
  "description": "描述文本"
}
```

---

## 向量入库流程

### 调用入口

```python
from app.services.vector_text_builder import ingest_vectors

# 批量入库
pairs = [(resource_obj, raw_dict), ...]
ingest_vectors(
    resource_type=ResourceType.component,
    pairs=pairs,
    skip_vector=False  # 为 True 时跳过入库
)
```

### 自动分批

- 每批 200 条数据（`_BATCH_SIZE = 200`）
- 调用 `vector_client.ingest()` 写入向量服务
- 失败不影响主流程，仅 warning 日志

### 数据格式

每条向量数据结构：
```json
{
  "data_id":  "唯一标识字符串",
  "text":     "可搜索文本",
  "metadata": {
    "name": "...",
    "其他字段": "..."
  }
}
```

### 向量服务API

**写入接口**: `POST /api/v1/ingest`
- Request: `{ "type": "component", "items": [data_id, text, metadata] }`
- Response: `{ "succeeded": [...], "failed": [...] }`

---

## 修改指引

| 改动内容 | 需修改的文件位置 |
|---------|----------------|
| 调整组件文本构造逻辑 | `vector_text_builder.py:38-53` (`build_component_text`) |
| 调整图标文本构造逻辑 | `vector_text_builder.py:75-83` (`build_icon_text`) |
| 调整插画文本构造逻辑 | `vector_text_builder.py:124-131` (`_build_illus_text_fn`) |
| 调整插画元数据字段 | `vector_text_builder.py:134-139` (`_build_illus_metadata`) |
| 修改翻译映射 | `storage/component/value_translations.json` |
| 修改元数据字段 | 对应类型的 `build_metadata` 函数 |
| 修改 data_id 来源 | `VectorSpec.get_data_id` lambda 函数 |
| 新增资源类型 | 在 `_build_registry()` 中添加新的 VectorSpec |

---

## 文件位置速查

| 文件 | 路径 | 说明 |
|------|------|------|
| 向量构造核心 | `app/services/vector_text_builder.py` | 所有类型的文本构造函数和注册表 |
| 向量客户端 | `app/clients/vector_client.py` | HTTP 调用向量服务 |
| 组件翻译表 | `storage/component/value_translations.json` | 组件属性值中文翻译 |
| 图标数据源 | `storage/icon/icons.json` | SVG 图标初始化数据 |
| 插画数据源 | `storage/illus/illus.json` | 插画初始化数据 |
| 模版数据源 | `storage/template/templates.json` | 模版初始化数据 |
| 组件索引 | `storage/component/*/component_index.json` | 组件库索引文件 |
| ORM 模型 | `app/models/resource.py` | 数据表定义 |
| 类型枚举 | `app/enums.py` | ResourceType 枚举定义 |

---

## 注意事项

1. **字段来源优先级**: 初始化入库时优先使用 `raw` 字典，更新场景 fallback 到 ORM 关联表
2. **翻译文件格式**: 支持 `key=value` 精确匹配和 `value` 通用匹配，前者优先级更高
3. **异常处理**: 向量入库失败不影响数据库写入，仅记录 warning 日志
4. **空值处理**: 所有构造函数都做了空值保护，缺失字段不会导致异常
5. **幂等性**: 使用 `data_id` 作为唯一标识，重复入库会覆盖旧数据