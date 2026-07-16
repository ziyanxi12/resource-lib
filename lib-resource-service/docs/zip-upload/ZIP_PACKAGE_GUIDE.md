# ZIP 包构建指南

本文档说明如何构建用于批量上传资源的 ZIP 包。

## 概述

资源库支持通过 ZIP 包批量上传以下资源类型：

| 类型 | type 值 | 说明 |
|------|---------|------|
| 组件 | `component` | 组件集 |
| 图标 | `icon` | SVG 图标 |
| 插画 | `illus` | 插画素材 |
| 模版 | `template` | 设计模版 |
| 图片 | `image` | 图片素材 |
| 文件 | `file` | 通用文件 |

## 上传限制

| 限制项 | 默认值 | 最大值 | 说明 |
|--------|--------|--------|------|
| 单次条目数 | 100 | 500 | 可通过环境变量配置，但有硬上限 |
| ZIP 包大小 | 50MB | 100MB | 超过最大值拒绝上传 |
| 单文件大小 | 10MB | 20MB | 防止异常大文件 |

**环境变量配置**（后端 `.env`）：
```env
MAX_UPLOAD_COUNT=100
MAX_ZIP_SIZE_MB=50
MAX_FILE_SIZE_MB=10
```

**注意**：配置值不能超过硬上限（500 条 / 100MB ZIP / 20MB 单文件）。

## ZIP 包结构

```
xxx.zip
├── config.json           # 必需，配置文件
├── {type}/               # 资源文件目录（按类型命名）
│   ├── a.svg
│   └── b.svg
└── image/                # 缩略图目录（固定名称）
    ├── a.png
    └── b.png
```

**示例：图标 ZIP 包**

```
icons-20240115.zip
├── config.json
├── icon/
│   ├── home.svg
│   ├── settings.svg
│   └── user.svg
└── image/
    ├── home.png
    ├── settings.png
    └── user.png
```

## config.json 格式

```json
{
  "meta": {
    "type": "icon",
    "source_id": 1
  },
  "data": [
    {
      "name": "首页图标",
      "group_id": 10,
      "width": 24,
      "height": 24,
      "file_path": "icon/home.svg",
      "file_url": "",
      "thumbnail_path": "image/home.png",
      "description": "首页导航图标",
      "tags": ["导航", "首页"],
      "search_text": "home 首页 主页",
      "raw_data": {}
    }
  ]
}
```

### meta 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型：`icon`/`illus`/`template`/`image`/`file` |
| `source_id` | number | 是 | 来源 ID，需先通过 API 获取 |

### data 数组字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 资源名称，不能为空 |
| `group_id` | number | 是 | 分组 ID，需先通过 API 获取或创建 |
| `width` | number | 是 | 宽度，必须为正数 |
| `height` | number | 是 | 高度，必须为正数 |
| `file_path` | string | 条件 | 文件在 ZIP 中的相对路径，与 `file_url` 至少填一个 |
| `file_url` | string | 条件 | 外部文件链接（如 Figma 链接），与 `file_path` 至少填一个 |
| `thumbnail_path` | string | 是 | 缩略图在 ZIP 中的相对路径 |
| `description` | string | 否 | 资源描述 |
| `tags` | string[] | 否 | 标签数组 |
| `search_text` | string | 否 | 搜索关键词 |
| `raw_data` | object | 否 | 自定义元数据，必须是对象 |

## 前置准备

### 1. 获取 source_id

```bash
GET /api/sources
```

响应：
```json
{
  "items": [
    { "id": 1, "name": "手动上传-图标", "resource_type": 3 },
    { "id": 2, "name": "Figma同步-图标", "resource_type": 3 }
  ]
}
```

根据 `resource_type` 筛选对应的来源，记录 `id`。

### 2. 获取 group_id

```bash
GET /api/groups?type=icon&source_id=1
```

响应：
```json
{
  "items": [
    {
      "id": 10,
      "name": "导航图标",
      "parent_id": null,
      "children": [
        { "id": 11, "name": "一级导航", "parent_id": 10 }
      ]
    }
  ]
}
```

### 3. 创建新分组（可选）

如果没有合适的分组，可以新建：

```bash
POST /api/groups
Content-Type: application/json

{
  "resource_type": 3,
  "source_id": 1,
  "name": "新分组名称",
  "parent_id": null
}
```

响应：
```json
{
  "id": 20,
  "name": "新分组名称",
  "parent_id": null
}
```

## 完整示例

### 图标 ZIP 包

**目录结构：**
```
icons.zip
├── config.json
├── icon/
│   ├── arrow-left.svg
│   ├── arrow-right.svg
│   └── search.svg
└── image/
    ├── arrow-left.png
    ├── arrow-right.png
    └── search.png
```

**config.json：**
```json
{
  "meta": {
    "type": "icon",
    "source_id": 1
  },
  "data": [
    {
      "name": "左箭头",
      "group_id": 10,
      "width": 24,
      "height": 24,
      "file_path": "icon/arrow-left.svg",
      "file_url": "",
      "thumbnail_path": "image/arrow-left.png",
      "description": "向左箭头图标",
      "tags": ["箭头", "方向"],
      "search_text": "arrow left 左",
      "raw_data": {}
    },
    {
      "name": "右箭头",
      "group_id": 10,
      "width": 24,
      "height": 24,
      "file_path": "icon/arrow-right.svg",
      "file_url": "",
      "thumbnail_path": "image/arrow-right.png",
      "description": "向右箭头图标",
      "tags": ["箭头", "方向"],
      "search_text": "arrow right 右",
      "raw_data": {}
    },
    {
      "name": "搜索",
      "group_id": 11,
      "width": 20,
      "height": 20,
      "file_path": "icon/search.svg",
      "file_url": "",
      "thumbnail_path": "image/search.png",
      "description": "搜索图标",
      "tags": ["搜索", "查找"],
      "search_text": "search 搜索 查找",
      "raw_data": {}
    }
  ]
}
```

### 图片 ZIP 包（仅链接）

如果资源是外部链接，可以不提供文件：

**config.json：**
```json
{
  "meta": {
    "type": "image",
    "source_id": 5
  },
  "data": [
    {
      "name": "Banner图",
      "group_id": 20,
      "width": 1920,
      "height": 1080,
      "file_path": "",
      "file_url": "https://example.com/banner.png",
      "thumbnail_path": "image/banner_thumb.png",
      "description": "首页 Banner",
      "tags": [],
      "search_text": "",
      "raw_data": {}
    }
  ]
}
```

## 验证脚本

使用 `validate.bundle.js` 验证 ZIP 包：

```bash
# 只验证 config.json 格式
node validate.bundle.js --json config.json

# 验证整个 ZIP 包（含文件存在性）
node validate.bundle.js --zip icons.zip
```

**成功输出：**
```
✓ config.json 格式正确
✓ 共 3 条记录，全部通过验证
```

**失败输出：**
```
✗ 验证失败

[第1条] name: 名称不能为空
[第2条] width: 必须为正数
[第3条] file_path: 文件不存在于 ZIP 包中 (icon/missing.svg)

共 3 条错误
```

## 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| ZIP 包中缺少 config.json | 未包含配置文件 | 在 ZIP 根目录添加 config.json |
| 类型不匹配 | config.json 中 type 与上传页面类型不符 | 确保 type 与页面对应 |
| 来源ID 不存在 | source_id 无效 | 先调用 `/api/sources` 获取有效 ID |
| 分组ID 不能为空 | group_id 缺失 | 先调用 `/api/groups` 获取或创建分组 |
| 宽/高必须为正数 | width/height 为 0 或负数 | 填写正确的尺寸 |
| 文件路径或链接至少填一个 | file_path 和 file_url 都为空 | 至少填写一个 |
| 缩略图路径不能为空 | thumbnail_path 缺失 | 提供缩略图路径 |
| 文件不存在于 ZIP 包中 | file_path 或 thumbnail_path 指向的文件不存在 | 检查文件路径是否正确 |

## 上传流程

1. 准备资源文件和缩略图
2. 编写 config.json
3. 运行验证脚本检查
4. 打包成 ZIP
5. 在前端上传页面选择 ZIP 文件
6. 确认信息无误后提交