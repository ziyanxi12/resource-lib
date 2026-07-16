# 资源库改造进度文档

> 本文档记录了资源库从 v1.0 到 v2.0 的改造进度。

---

## 📅 改造日期

- **开始时间**：2026-07-15
- **完成时间**：2026-07-15
- **当前状态**：✅ 改造完成

---

## 🎯 改造目标

根据 `docs/Design_v1.0.md` 的设计方案，实现：

1. ✅ **数据与业务分离**：删除详情表，使用 `raw_data` 存储原始数据
2. ✅ **统一入库模板**：所有资源类型使用统一的字段结构
3. ✅ **向量智能检索**：新增向量搜索接口（三种响应模式）
4. ✅ **层级分类管理**：新增来源管理，分组按来源独立
5. ✅ **统一上传架构**：所有类型使用统一的上传接口

---

## ✅ 已完成的工作

### Phase 1: 数据库模型重构 ✅

#### 删除的表
- ❌ `component_variants` 表（组件变体详情表）
- ❌ `resource_icons` 表（SVG 图标详情表）
- ❌ `resource_illus` 表（插画详情表）

#### 新增的表
- ✅ `resource_sources` 表（来源管理表）
- ✅ `resource_groups` 表（分组表，重构）

#### 调整的表结构

**resources 主表**：
- ❌ 删除字段：`raw_data`, `mime_type`
- ✅ 新增字段：`source_id`（必填）, `file_url`, `file_type`, `search_text`, `vector_text`, `raw_data`

**resource_groups 分组表**：
- ✅ 新增字段：`source_id`（分组按来源独立）

---

### Phase 2: 后端业务逻辑重构 ✅

#### 删除的文件
- ❌ `services/component_service.py`
- ❌ `services/icon_service.py`
- ❌ `services/illus_service.py`
- ❌ `services/template_service.py`
- ❌ `services/image_service.py`
- ❌ `services/file_service.py`
- ❌ `routers/component.py`
- ❌ `routers/icon.py`
- ❌ `routers/template.py`
- ❌ `routers/image.py`
- ❌ `routers/file.py`
- ❌ `schemas/component.py`
- ❌ `schemas/icon.py`
- ❌ `schemas/illus.py`
- ❌ `schemas/template.py`
- ❌ `schemas/image.py`
- ❌ `schemas/file.py`
- ❌ `clients/external.py`（部分删除）

#### 新增的文件
- ✅ `services/upload_service.py`（统一上传服务）
- ✅ `services/source_service.py`（来源管理）
- ✅ `services/group_service.py`（分组管理）
- ✅ `services/vector_sync_service.py`（向量同步）
- ✅ `services/vector_text_builder.py`（向量文本构建）
- ✅ `routers/upload.py`（统一上传路由）
- ✅ `routers/sources.py`（来源管理路由）
- ✅ `routers/group.py`（分组管理路由）
- ✅ `routers/search.py`（向量搜索路由）
- ✅ `schemas/upload.py`（上传响应模型）
- ✅ `schemas/source.py`（来源管理模型）
- ✅ `schemas/group.py`（分组管理模型）
- ✅ `clients/vector_client.py`（向量服务客户端）

#### 重写的文件
- ✅ `services/resource_service.py` - 通用 CRUD，新增 `build_vector_text`
- ✅ `services/init_service.py` - 适配新表结构
- ✅ `routers/resources.py` - 通用资源路由
- ✅ `routers/vector_router.py` - 向量服务代理
- ✅ `main.py` - 注册新路由

---

### Phase 3: 前端改造 ✅

#### 新增的文件
- ✅ `pages/ResourceManage.tsx`（统一管理页面）
- ✅ `pages/ResourceUpload.tsx`（统一上传页面，支持 ZIP）
- ✅ `components/ResourceTable.tsx`（统一表格组件）
- ✅ `components/GroupTree.tsx`（分组树组件）
- ✅ `components/DetailDrawer.tsx`（详情侧边栏）

#### 删除的文件
- ❌ `pages/ComponentManage.tsx`
- ❌ `pages/TemplateManage.tsx`
- ❌ `pages/SVGManage.tsx`
- ❌ `pages/IllustrationManage.tsx`
- ❌ `pages/ImageManage.tsx`
- ❌ `pages/FileManage.tsx`
- ❌ 相关的 BatchUpload 页面

#### 重写的文件
- ✅ `api.ts` - 统一 `batchUpload` 接口
- ✅ `App.tsx` - 统一导航和路由

---

### Phase 4: 统一上传架构重构 ✅

#### 后端改造
- ✅ 新建 `upload_service.py` - 统一批量上传服务
- ✅ 新建 `routers/upload.py` - 统一上传路由
- ✅ 新建 `schemas/upload.py` - 统一响应模型
- ✅ 删除旧的类型专属文件（icon/illus/template/image/file 的 service/router/schema）
- ✅ 将 `understand_image` 功能移到 `upload_service.py`

#### 前端改造
- ✅ `api.ts` - 合并为统一接口 `batchUpload(type, formData)`
- ✅ `ResourceManage.tsx` - 所有类型显示 ZIP 上传按钮
- ✅ `ResourceUpload.tsx` - 统一调用 `api.batchUpload(type, formData)`

---

### Phase 5: 文档更新 ✅

- ✅ `CLAUDE.md` - 更新项目结构说明
- ✅ `lib-resource-service/README.md` - 更新 API 接口文档
- ✅ `lib-resource-service/DESIGN.md` - 更新设计文档
- ✅ `lib-resource-service/DATABASE.md` - 反映 v2.0 数据库结构
- ✅ `docs/PROGRESS.md` - 更新进度记录

---

## 🎉 改造总结

### 架构变化

| 方面 | v1.0 | v2.0 |
|------|------|------|
| 数据库 | 详情表分离 | 统一主表 + raw_data |
| 上传接口 | 类型专属接口 | 统一 `/api/upload?type=xxx` |
| 前端页面 | 类型专属页面 | 统一管理/上传页面 |
| 来源管理 | 无 | 必填来源 |
| 分组管理 | 全局分组 | 按来源独立 |

### 核心改进

1. **统一上传架构**：所有类型使用同一套上传逻辑，减少代码重复
2. **数据与业务分离**：原始数据存储在 `raw_data`，业务字段独立
3. **来源追溯**：每个资源必须关联来源，便于数据管理
4. **分组隔离**：不同来源有独立的分组树，避免数据混乱

---

## 📝 重要注意事项

### 1. 向量文本构建逻辑

```python
vector_text = name + description + tags + search_text
```

### 2. 上传接口必填参数

- `source_id` - 来源ID（必填）
- `files` - 资源文件列表
- `thumbnails` - 缩略图列表（PNG）
- `items` - JSON 元数据数组

### 3. ZIP 上传格式

```
test_upload.zip
├── config.json          # 元数据
├── icon/                # 资源文件
│   ├── abc.svg
│   └── def.svg
└── image/               # 缩略图
    ├── abc_thumb.png
    └── def_thumb.png
```

config.json 格式：
```json
{
  "meta": {
    "type": "icon",
    "source_id": 1
  },
  "data": [
    {
      "name": "图标名",
      "group_id": 1,
      "width": 24,
      "height": 24,
      "file_path": "icon/abc.svg",
      "thumbnail_path": "image/abc_thumb.png",
      "tags": ["标签1"],
      "search_text": "关键词",
      "meta_json": {}
    }
  ]
}
```

---

## 📚 相关文档

- 设计文档：`docs/Design_v1.0.md`
- 资源模版：`docs/resource_template.json`
- 项目说明：`CLAUDE.md`
- 数据库文档：`lib-resource-service/DATABASE.md`

---

**文档版本**：v2.0  
**最后更新**：2026-07-15  
**维护者**：opencode AI assistant