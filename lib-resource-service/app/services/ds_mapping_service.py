"""组件 ↔ Pixso 映射服务（ds_component_mapping 表）

- sync_html_components：HTML 组件清单入库/同步。数据源优先级：{slug}/assets/components/index.json
  （组件包落盘清单，含 shortNames 中文名）；缺失时兜底 {slug}/design-system.json 的
  components.items[]（历史存量系统无组件包——zh 留空，编辑弹窗可写 html_zh 补）。
  新组件插入 missing 行、已有行只更新中文名/分组（Pixso 数据与 status 不动）、
  清单里已不存在的组件行删除（组件没了映射无意义）。
  触发：组件包 ingest 成功后自动挂钩（import_parts 内）+ POST /{slug}/mapping/sync 手动补（存量系统）。
- get_mapping：读整表（渲染端消费，GET /{slug}/mapping 公开）。
"""

import json
import logging
import os
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.design_system import DesignSystem
from app.models.ds_component_mapping import DsComponentMapping

logger = logging.getLogger(__name__)

# sync 时允许更新/保留的 HTML 侧字段（Pixso 侧与 status 恒不触碰）
_HTML_FIELDS = ("html_zh", "html_group")


def _index_json_path(slug: str) -> str:
    """组件包落盘 index.json 绝对路径（{slug}/assets/components/index.json）"""
    return os.path.join(settings.FILE_ROOT_DIR, "design-systems", slug, "assets", "components", "index.json")


def _load_component_index(slug: str) -> Optional[List[Dict]]:
    """读组件清单并归一化为 [{name, zh, group}]；两处数据源皆无/坏 JSON → None（sync 静默跳过）。

    数据源优先级（历史存量系统均无组件包，② 为发布链路的兜底建表来源）：
    ① {slug}/assets/components/index.json——组件包落盘清单：
       - items 路径形如「操作类/Button/spec.json」→ group=操作类 / name=Button；
         无目录层级（GTS 之外的老格式）→ group=""
       - 中文名：shortNames[name] 优先（key 为组件英文名）；无则空（展示端自行回落 spec title）
    ② {slug}/design-system.json 的 components.items[]——历史存量兜底（无组件包）：
       - name=items[].name；group=group 数组首段（与 ① 语义对齐）；zh=""（编辑弹窗可写 html_zh 补）
    - name 去重（同名取首条，防脏清单产生 UNIQUE 冲突）
    """
    path = _index_json_path(slug)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                ix = json.load(f)
        except (ValueError, OSError) as e:
            logger.warning("[mapping-sync] %s index.json 读取失败（跳过同步）：%s", slug, e)
            return None
        items = ix.get("items")
        if not isinstance(items, list):
            return None
        short_names = ix.get("shortNames") if isinstance(ix.get("shortNames"), dict) else {}
        out, seen = [], set()
        for raw in items:
            if not isinstance(raw, str) or not raw.strip():
                continue
            parts = raw.replace("\\", "/").split("/")
            name = parts[-2] if len(parts) >= 2 and parts[-1] == "spec.json" else ""
            if not name or name in seen:
                continue
            seen.add(name)
            out.append({"name": name, "zh": str(short_names.get(name) or ""), "group": parts[0] if len(parts) >= 3 else ""})
        return out

    # ② 历史存量兜底：无组件包清单 → 从 design-system.json 的组件区读（zh 空，编辑弹窗可补）
    ds_path = os.path.join(settings.FILE_ROOT_DIR, "design-systems", slug, "design-system.json")
    if not os.path.isfile(ds_path):
        return None
    try:
        with open(ds_path, "r", encoding="utf-8") as f:
            ds = json.load(f)
    except (ValueError, OSError) as e:
        logger.warning("[mapping-sync] %s design-system.json 读取失败（跳过同步）：%s", slug, e)
        return None
    items = ((ds or {}).get("components") or {}).get("items")
    if not isinstance(items, list):
        return None
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        g = it.get("group")
        group = g[0] if isinstance(g, list) and g else (str(g) if g else "")
        out.append({"name": name, "zh": "", "group": group})
    return out or None


def sync_html_components(db: Session, slug: str, operator: Optional[str] = None) -> Dict:
    """HTML 组件清单 → 映射表 upsert（全量同步语义）。

    返回 {"added": n, "updated": n, "removed": n, "total": n}；无清单 → {"total": 现存行数, "skipped": True}。
    任何异常向上抛（自动挂钩处 try/except 吞掉；手动接口转 500/400 由路由层处理）。
    """
    comps = _load_component_index(slug)
    if comps is None:
        total = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).count()
        return {"added": 0, "updated": 0, "removed": 0, "total": total, "skipped": True}

    rows = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).all()
    by_name = {r.component_name: r for r in rows}

    added = updated = removed = 0
    wanted = {c["name"] for c in comps}
    # ① 清单里已不存在的组件行删除
    for r in rows:
        if r.component_name not in wanted:
            db.delete(r)
            removed += 1
    # ② upsert：已有行只刷 HTML 侧字段（Pixso 数据与 status 保留），新组件插入 missing 行
    for c in comps:
        row = by_name.get(c["name"])
        if row is not None:
            if (row.html_zh or "") != c["zh"] or (row.html_group or "") != c["group"]:
                row.html_zh, row.html_group = c["zh"] or None, c["group"] or None
                row.updated_by = operator
                updated += 1
        else:
            db.add(DsComponentMapping(
                slug=slug, component_name=c["name"],
                html_zh=c["zh"] or None, html_group=c["group"] or None,
                status="missing", created_by=operator, updated_by=operator,
            ))
            added += 1
    db.commit()
    total = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).count()
    logger.info("[mapping-sync] slug=%s：新增 %d / 更新 %d / 删除 %d / 现存 %d",
                slug, added, updated, removed, total)
    return {"added": added, "updated": updated, "removed": removed, "total": total}


def _parse_json_field(val: Optional[str]) -> Optional[dict]:
    """instance_spec 列安全解析（坏 JSON → None，不炸整页）"""
    if not val:
        return None
    try:
        out = json.loads(val)
        return out if isinstance(out, dict) else None
    except ValueError:
        return None


def get_mapping(db: Session, slug: str) -> Dict:
    """整表读取：{slug, count, items:[{component_name, html_zh, html_group,
    pixso_name, pixso_guid, status, match_type, url, pixso_category, instance_spec(已解析), instance_code}]}。
    无行 → count 0。"""
    q = db.query(DesignSystem).filter(DesignSystem.slug == slug, DesignSystem.is_deleted == 0).first()
    if not q:
        return {"slug": slug, "count": 0, "items": []}
    rows = (
        db.query(DsComponentMapping)
        .filter(DsComponentMapping.slug == slug)
        .order_by(DsComponentMapping.component_name)
        .all()
    )
    items = [{
        "component_name": r.component_name,
        "html_zh": r.html_zh or "",
        "html_group": r.html_group or "",
        "pixso_name": r.pixso_name,
        "pixso_guid": r.pixso_guid,
        "pixso_category": r.pixso_category,
        "file_key": r.file_key,
        "match_type": r.match_type,
        "url": r.url,
        "thumbnail_url": r.thumbnail_url,
        "status": r.status or "missing",
        "instance_spec": _parse_json_field(r.instance_spec),
        "instance_code": r.instance_code,
    } for r in rows]
    return {"slug": slug, "count": len(items), "items": items}


# PUT /{slug}/mapping 可写字段：Pixso 侧全量 + html_zh（编辑弹窗写组件中文名；其余 HTML 侧
# 字段 html_group 只归 sync；component_name 为 join 键不可改）。thumbnail_url 为匹配时刻从
# 组件库清单拷贝的缩略图相对路径（渲染端拼 origin+/api 前缀访问）
_UPDATABLE_FIELDS = (
    "html_zh",
    "pixso_name", "pixso_guid", "file_key", "page_id", "page_name", "pixso_category",
    "component_content_key", "match_type", "status", "url", "instance_spec", "instance_code",
    "thumbnail_url",
)


def put_mapping(db: Session, slug: str, items: List[Dict], operator: Optional[str] = None) -> Dict:
    """匹配结果批量回填（merge 语义，匹配脚本调用）。

    - 按 component_name upsert：行不存在 → 400（组件清单先经 sync 入表，映射只回填已有行）；
      行存在 → 覆盖 _UPDATABLE_FIELDS 中请求提供的字段（未提供的字段不动）
    - **manual 保护**：存量行 match_type == "manual" 且请求项 match_type != "manual"（批量匹配
      重跑通道）→ 跳过不覆盖（人工修正成果）；请求项自身带 match_type == "manual"（编辑弹窗的
      人工编辑通道）→ 放行——人工行允许继续人工编辑
    - instance_spec 传 dict 自动 dumps（字符串原样存）；status/match_type 不校验枚举（前端枚举展示）
    - 返回 {"total": 行数, "updated": n, "skipped_manual": n, "missing": n, "aligned": n, "partial": n}
    """
    rows = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).all()
    by_name = {r.component_name: r for r in rows}
    unknown = [it.get("component_name") for it in items if not it.get("component_name") or it["component_name"] not in by_name]
    if unknown:
        raise ValueError("以下组件不在映射表中（请先 POST /{slug}/mapping/sync 同步组件清单）：%s"
                         % "、".join(sorted(set(unknown))))

    updated = skipped = 0
    status_stat = {"aligned": 0, "partial": 0, "missing": 0}
    for it in items:
        row = by_name[it["component_name"]]
        if row.match_type == "manual" and it.get("match_type") != "manual":
            skipped += 1
            status_stat[row.status or "missing"] = status_stat.get(row.status or "missing", 0) + 1
            continue
        for f in _UPDATABLE_FIELDS:
            if f in it and it[f] is not None:
                val = it[f]
                if f == "instance_spec" and isinstance(val, dict):
                    val = json.dumps(val, ensure_ascii=False)
                setattr(row, f, val)
        row.updated_by = operator
        updated += 1
        status_stat[row.status or "missing"] = status_stat.get(row.status or "missing", 0) + 1
    db.commit()
    total = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).count()
    logger.info("[mapping-put] slug=%s：更新 %d / manual 跳过 %d / 现存 %d",
                slug, updated, skipped, total)
    return {"total": total, "updated": updated, "skipped_manual": skipped,
            "aligned": status_stat.get("aligned", 0),
            "partial": status_stat.get("partial", 0),
            "missing": status_stat.get("missing", 0)}


# ─────────────────────────── design-system.json 投影（v4.4 mapping 键注入） ───────────────────────────

def _library_name() -> str:
    """来源库名：pixso-thumbs/library.json（组件库全局信息约定文件）；缺失 → 空串。"""
    path = os.path.join(settings.FILE_ROOT_DIR, "design-systems", "pixso-thumbs", "library.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return str(data.get("libraryName") or "")
    except (ValueError, OSError):
        return ""


def inject_mapping(db: Session, slug: str) -> bool:
    """把 DB 映射行投影进 design-system.json 的 mapping / mappingLibraryName 键。

    - DB 为唯一可写源（PUT mapping / sync / import_parts 自动重建后调用本函数刷新投影）
    - 无映射行 → 不写 mapping 键（模板保持两列）；有行 → per-name 字典
      {component_name: {pixso_name, pixso_guid, url, status}}（模板第三列「关联设计组件」直读）
    - json 缺失/损坏 → 静默跳过（不阻塞调用方；import_parts 重建后再刷即可）
    - 幂等：重复调用覆盖同键
    """
    path = os.path.join(settings.FILE_ROOT_DIR, "design-systems", slug, "design-system.json")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
    except (ValueError, OSError) as e:
        logger.warning("[mapping-inject] %s design-system.json 读取失败（跳过注入）：%s", slug, e)
        return False

    rows = db.query(DsComponentMapping).filter(DsComponentMapping.slug == slug).all()
    if rows:
        data["mapping"] = {r.component_name: {
            "pixso_name": r.pixso_name, "pixso_guid": r.pixso_guid,
            "url": r.url, "status": r.status or "missing",
            "thumbnail_url": r.thumbnail_url,
        } for r in rows}
        data["mappingLibraryName"] = _library_name()
    else:
        data.pop("mapping", None)
        data.pop("mappingLibraryName", None)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return True
    except OSError as e:
        logger.warning("[mapping-inject] %s design-system.json 写入失败：%s", slug, e)
        return False
