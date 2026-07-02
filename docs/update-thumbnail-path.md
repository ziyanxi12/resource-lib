# 更新 Icon / Illus 缩略图路径 SQL

脚本生成缩略图后，以资源的原始 ID 命名文件（如 `100.png`、`EMPLY_ILL.png`），
通过以下 SQL 批量回写 `resources.thumbnail_path` 字段。

---

## 表关系说明

```
resources (主表)
    id, resource_type, thumbnail_path, is_deleted, ...

resource_icons (icon 详情，resource_type = 3)
    icon_id      ← 原始 JSON 中的 id，也是缩略图文件名
    resource_id  ← 关联 resources.id

resource_illus (illus 详情，resource_type = 4)
    illus_id     ← 原始 JSON 中的 id，也是缩略图文件名
    resource_id  ← 关联 resources.id
```

---

## MySQL 版本

### 测试版（先改 5 条，确认无误再执行全量）

```sql
-- Icon：先改 5 条
UPDATE resources r
JOIN resource_icons ri ON ri.resource_id = r.id
SET r.thumbnail_path = CONCAT('icon/thumbnails/', ri.icon_id, '.png')
WHERE r.resource_type = 3
  AND r.is_deleted = 0
LIMIT 5;

-- Illus：先改 5 条
UPDATE resources r
JOIN resource_illus ri ON ri.resource_id = r.id
SET r.thumbnail_path = CONCAT('illus/thumbnails/', ri.illus_id, '.png')
WHERE r.resource_type = 4
  AND r.is_deleted = 0
LIMIT 5;
```

执行后用以下 SQL 验证结果：

```sql
SELECT id, name, resource_type, thumbnail_path
FROM resources
WHERE resource_type IN (3, 4)
  AND thumbnail_path IS NOT NULL
LIMIT 10;
```

---

### 全量版（确认无误后执行）

#### 更新 Icon 缩略图路径（resource_type = 3）

```sql
UPDATE resources r
JOIN resource_icons ri ON ri.resource_id = r.id
SET r.thumbnail_path = CONCAT('icon/thumbnails/', ri.icon_id, '.png')
WHERE r.resource_type = 3
  AND r.is_deleted = 0;
```

**说明：**
- `JOIN resource_icons` — 通过 `resource_id` 把主表和 icon 详情表连起来
- `CONCAT(...)` — 拼接出完整的相对路径，如 `icon/thumbnails/100.png`
- `resource_type = 3` — 只处理 SVG/Icon 类型
- `is_deleted = 0` — 跳过已软删除的记录

#### 更新 Illus 缩略图路径（resource_type = 4）

```sql
UPDATE resources r
JOIN resource_illus ri ON ri.resource_id = r.id
SET r.thumbnail_path = CONCAT('illus/thumbnails/', ri.illus_id, '.png')
WHERE r.resource_type = 4
  AND r.is_deleted = 0;
```

**说明：**
- 逻辑与 Icon 相同，只是关联表和类型编号不同
- 拼接结果示例：`illus/thumbnails/EMPLY_ILL.png`

---

## SQLite 版本（本地 dev.db）

SQLite 不支持 UPDATE...JOIN，改用子查询；字符串拼接用 `||` 代替 `CONCAT()`。

```sql
-- Icon
UPDATE resources
SET thumbnail_path = (
    SELECT 'icon/thumbnails/' || icon_id || '.png'
    FROM resource_icons
    WHERE resource_icons.resource_id = resources.id
)
WHERE resource_type = 3
  AND is_deleted = 0
  AND EXISTS (SELECT 1 FROM resource_icons WHERE resource_icons.resource_id = resources.id);

-- Illus
UPDATE resources
SET thumbnail_path = (
    SELECT 'illus/thumbnails/' || illus_id || '.png'
    FROM resource_illus
    WHERE resource_illus.resource_id = resources.id
)
WHERE resource_type = 4
  AND is_deleted = 0
  AND EXISTS (SELECT 1 FROM resource_illus WHERE resource_illus.resource_id = resources.id);
```

---

## 执行方式

**MySQL：**
```bash
mysql -u <user> -p <db_name> < update-thumbnail-path.sql
# 或直接在 MySQL 客户端粘贴执行
```

**SQLite（本地调试）：**
```bash
sqlite3 lib-resource-service/dev.db < update-thumbnail-path.sql
```

---

## 注意事项

- **路径前缀**（`icon/thumbnails/`）和**文件后缀**（`.png`）需与生成脚本保持一致，如有不同请相应修改
- `thumbnail_path` 存的是相对于 `FILE_ROOT_DIR` 的路径，前端/后端通过 `/static/` 前缀拼接成完整 URL
- 两条 SQL 可安全重复执行（幂等），路径相同时覆盖写入无副作用
