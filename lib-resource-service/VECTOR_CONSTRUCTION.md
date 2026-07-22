# 向量数据构造说明

本文档描述向量库的实际数据结构、CRUD 全路径，以及已知缺口与改进建议。

---

## 1. 总览

所有资源的向量数据通过 `app/services/vector_text_builder.py` 的 `ingest_vectors()` 函数统一入库，6 种资源类型（component / template / icon / illus / image / file）走**完全相同**的 payload 结构。

- **唯一入库入口**: `ingest_vectors()` (`vector_text_builder.py:13-67`)
- **开关**: 受 `settings.VECTOR_SERVICE_ENABLED` 控制，关闭时直接 return
- **vec_type 映射**: 仅决定向量服务的 collection 名，不影响 payload 内容

| ResourceType | vec_type 字符串 |
|--------------|----------------|
| component (1) | `component` |
| template (2) | `template` |
| icon (3) | `icon` |
| illus (4) | `illustration` |
| image (5) | `image` |
| file (6) | `file` |

---

## 2. 统一 payload 结构

每条向量数据结构：

```json
{
  "data_id":  "123",
  "text":     "资源名称 描述文本 标签1 标签2 搜索关键词",
  "metadata": {
    "source_id": 1,
    "group_id":  2
  }
}
```

### 字段用途：搜索 vs 筛选

| 字段 | 取值 | 用途 | 改动是否需要重新 embedding |
|------|------|------|---------------------------|
| `data_id` | `str(Resource.id)` | 唯一标识，用于去重 / 覆盖 / 删除 / 反查 | — |
| `text` | `res.vector_text or build_vector_text(res)` | **向量搜索**（语义 + 全文检索的输入） | **是** |
| `metadata.source_id` | `res.source_id` | **向量筛选**（精确过滤） | **否** |
| `metadata.group_id` | `res.group_id` | **向量筛选**（精确过滤） | **否** |

**关键区分**：

- **搜索字段**：只有 `text`。修改 `name` / `description` / `tags` / `search_text` 会改变 `text` 内容，从而影响搜索召回，需要重新 embedding。
- **筛选字段**：只有 `metadata.source_id` 和 `metadata.group_id`。修改它们只影响过滤条件，不影响搜索召回和排序，**不需要重新 embedding**。
- **搜索时**：`text` 走向量服务的语义 / 全文检索；`metadata` 作为 filters 传入向量服务做预过滤。`group_id` 筛选时会自动展开为包含所有后代分组的 id 列表（见 `vector_router.py:212-216`）。

---

## 3. text 构造逻辑

**函数**: `build_vector_text()` (`resource_service.py:322-334`)

所有资源类型使用**同一个**函数，拼接公式：

```
text = name + description + tags(空格连接) + search_text
```

```python
def build_vector_text(resource: Resource) -> str:
    tags_str = ' '.join([t.tag for t in resource.tags])
    parts = [
        resource.name or '',
        resource.description or '',
        tags_str,
        resource.search_text or ''
    ]
    vector_text = ' '.join(filter(None, parts))
    return ' '.join(vector_text.split())
```

入库时优先使用 DB 中已缓存的 `res.vector_text`，为空时 fallback 到 `build_vector_text(res)` 实时计算：

```python
"text": res.vector_text or build_vector_text(res)
```

---

## 4. 向量 CRUD 全路径

### 新增

| 操作 | API 入口 | DB 处理 | 向量库处理 | 即时同步 |
|------|---------|---------|-----------|---------|
| 初始化入库 | `POST /api/init` | 批量插入 Resource | `ingest_vectors` + `batch_update_vector_time` | ✅ |
| 批量上传 | `POST /api/upload?type=...` | 批量插入 Resource + Tags | `ingest_vectors` + `batch_update_vector_time` | ✅ |

**入库流程**：

```
init_service / upload_service
  → build_vector_text(res) 写入 res.vector_text
  → db.commit()
  → ingest_vectors(resource_type, pairs)
    → vector_client.ingest(vec_type, items)
      → 每 200 条一批 POST /api/v1/ingest
  → batch_update_vector_time(db, resource_ids)
```

### 修改

| 操作 | API 入口 | 改了什么 | 更新 `data_updated_at` | 向量库处理 | 即时同步 |
|------|---------|---------|----------------------|-----------|---------|
| 编辑单资源 | `PUT /api/resources/{id}` | name / desc / tags / search_text | ✅ | 靠 `sync-vectors` 兜底 re-embedding | ❌ 手动触发 |
| 编辑单资源 | `PUT /api/resources/{id}` | group_id | ❌ | `vector_client.update(metadata)` | ✅ |
| 编辑单资源 | `PUT /api/resources/{id}` | text 字段 + group_id | ✅ | 靠 `sync-vectors` 兜底（ingest 覆盖 text + metadata） | ❌ 手动触发 |
| 批量移动分组 | `PUT /api/resources/batch-move` | group_id | ❌ | `vector_client.update(metadata)` 逐条更新 | ✅ |
| 增量同步 | `POST /api/resources/sync-vectors` | 按 `vector_updated_at < data_updated_at` 筛选 | — | `ingest_vectors` | 手动触发 |
| 全量重建 | `POST /api/vector/rebuild` | 全部数据 | — | `ingest_vectors` | 手动触发 |

**`data_updated_at` 更新规则**：仅当 text 相关字段（name / description / tags / search_text）变更时更新。改 group_id 或其他字段（file_name / thumbnail 等）不更新，避免触发不必要的 re-embedding。

**group_id 即时同步**：改 group_id 时通过 `vector_client.update(metadata=...)` 只更新向量库 metadata，不触发 re-embedding，也不更新 `vector_updated_at`。若同时改了 text 字段，则不走此路径，由 `sync-vectors` 统一 re-embedding（ingest 全量覆盖会同时更新 text 和 metadata）。

### 删除

| 操作 | API 入口 | 向量库处理 | 即时同步 |
|------|---------|-----------|---------|
| 单条删除 | `DELETE /api/resources/{id}` | `vector_client.delete(vec_type, data_id)` | ✅ |
| 批量删除（按筛选） | `DELETE /api/resources/batch` | `vector_client.batch_delete(vec_type, data_ids)` | ✅ |
| 批量删除（按 ID 列表） | `DELETE /api/resources/batch-ids` | `vector_client.batch_delete(vec_type, data_ids)` | ✅ |

### 查询

| 操作 | API 入口 | 说明 |
|------|---------|------|
| 向量搜索 | `POST /api/vector/search` | `vector_client.batch_search` + DB 反查 enrichment，支持 `basic` / `normal` / `complete` 三种响应模式 |
| LLM 搜索 | `POST /api/vector/search/llm` | 精简版，仅返回 `data_id` + `vector_text` + `score` |
| 详情查询 | `GET /api/vector/detail` | 纯 DB 反查（通过 data_id 查 Resource），不查向量库 |

**搜索响应模式**：

| 模式 | 返回字段 | 适用场景 |
|------|---------|---------|
| `basic` | `id`, `vector_text`, `score` | LLM 专用 |
| `normal` | `id`, `vector_text`, `score`, `raw_data` | 外部系统调用 |
| `complete` | 全量资源字段 + `vector_text` + `score` | 前端展示（默认） |

---

## 5. 修改 vector_text vs 修改 group_id

这两种改动的本质不同，处理方式也应不同：

| 改动内容 | 影响搜索？ | 影响筛选？ | 是否需要 re-embedding | 理想做法 |
|---------|----------|----------|----------------------|---------|
| 改 name / desc / tags / search_text | ✅ | ❌ | **是** | `ingest_vectors` 覆盖（重新 embedding + 写 text） |
| 改 group_id | ❌ | ✅ | **否** | `vector_client.update(metadata=...)` 只更新 metadata |

**核心区别**：

- 改 `vector_text` → 搜索内容变了，**必须重新 embedding**，否则搜不到新内容
- 改 `group_id` → 搜索内容没变，只是筛选条件变了，**不需要重新 embedding**，只需更新向量库的 `metadata.group_id`

`vector_client.update()`（`vector_client.py:245-278`）支持只传 `metadata` 不传 `text`，向向量服务发 `PUT /api/v1/update` 即可只改 metadata 不触发 embedding。业务代码在 group_id 变更场景（`PUT /{id}` 和 `batch-move`）已调用此方法。

### 当前实际处理对比

| 场景 | API | 实际处理 | 是否正确 |
|------|-----|---------|---------|
| 改 text 字段 | `PUT /api/resources/{id}` | 更新 DB + `data_updated_at`，靠 `sync-vectors` 兜底 re-embedding | ✅ 设计如此 |
| 改 group_id（仅 group_id） | `PUT /api/resources/{id}` | 即时 `vector_client.update(metadata)`，不 re-embedding | ✅ |
| 改 text + group_id | `PUT /api/resources/{id}` | 更新 `data_updated_at`，靠 `sync-vectors` 兜底（ingest 覆盖 text + metadata） | ✅ |
| 改 group_id | `PUT /api/resources/batch-move` | 逐条 `vector_client.update(metadata)`，不 re-embedding | ✅ |

---

## 6. 设计说明

### text 字段变更：延迟同步

`PUT /api/resources/{id}` 改 text 相关字段（name / description / tags / search_text）后，不即时调 `ingest_vectors`，而是更新 `data_updated_at`，由 `sync-vectors` 增量同步兜底。这是设计决策：re-embedding 较耗时，适合批量异步处理，不宜在单条编辑接口中同步等待。

### group_id 变更：即时同步 metadata

`PUT /api/resources/{id}` 和 `batch-move` 改 group_id 后，即时调 `vector_client.update(metadata=...)` 只更新向量库 metadata，不触发 re-embedding，不更新 `vector_updated_at`。这样 sync-vectors 不会因为 group_id 变更而误判需要 re-embedding。

### 未使用项

| 项目 | 位置 | 说明 |
|------|------|------|
| `raw` dict | `ingest_vectors` 的 `pairs` 参数 | 入参包含 `raw` 但入库时未读取，初始化 JSON 原始字段未进向量库 |
| `value_translations.json` | `config.py:46-49` 加载 | 翻译表在 config 中加载，但向量构造代码未引用 |

---

## 7. 修改指引

| 改动内容 | 需修改的文件:行 |
|---------|----------------|
| 调整 text 拼接逻辑 | `resource_service.py:322-334` (`build_vector_text`) |
| 调整 metadata 字段 | `vector_text_builder.py:51-54` |
| 调整 data_id 取值 | `vector_text_builder.py:49` |
| 修改入库分批大小 | `vector_client.py:18` (`_BATCH_SIZE = 200`) |
| 修改增量同步批次大小 | `vector_sync_service.py:96` (`_SYNC_BATCH_SIZE = 100`) |
| 修改搜索响应模式 | `vector_router.py:109-133` (`_build_*_response`) |
| 新增资源类型 | `vector_text_builder.py:34-41` 加 vec_type 映射 |

---

## 8. 文件位置速查

| 文件 | 路径 | 说明 |
|------|------|------|
| 向量入库入口 | `app/services/vector_text_builder.py` | `ingest_vectors()` 统一入库 |
| 向量文本构造 | `app/services/resource_service.py` | `build_vector_text()` 拼接 text |
| 向量 HTTP 客户端 | `app/clients/vector_client.py` | ingest / search / update / delete |
| 向量同步服务 | `app/services/vector_sync_service.py` | 缺失检测 + 增量同步 |
| 向量搜索路由 | `app/routers/vector_router.py` | search / detail / rebuild / sync |
| 资源路由（CRUD） | `app/routers/resources.py` | 资源增删改查 + 向量同步触发 |
| 上传服务 | `app/services/upload_service.py` | 批量上传 + 向量入库 |
| 初始化服务 | `app/services/init_service.py` | 组件集初始化 + 向量入库 |
| ORM 模型 | `app/models/resource.py` | 数据表定义 |
| 类型枚举 | `app/enums.py` | ResourceType 枚举定义 |

---

## 9. 注意事项

1. **幂等性**: 使用 `data_id`（即 `Resource.id`）作为唯一标识，重复入库会覆盖旧数据
2. **异常隔离**: 向量入库失败不影响数据库写入，仅记录 warning 日志
3. **空值保护**: `build_vector_text` 对所有字段做了空值保护，缺失字段不会导致异常
4. **时间戳机制**: `data_updated_at` 仅在 text 相关字段（name / description / tags / search_text）变更时更新，`vector_updated_at` 记录向量 re-embedding 同步时间。增量同步通过对比两者筛选待同步数据。改 group_id 不更新 `data_updated_at`，避免触发不必要的 re-embedding
5. **group_id 筛选展开**: 搜索时传入 `group_id` 过滤条件会自动展开为包含所有后代分组的 id 列表（`vector_router.py:212-216`）
