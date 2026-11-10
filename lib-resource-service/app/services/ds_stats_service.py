"""设计系统打点统计聚合（管理台数据统计页数据源）

口径约定：
- 时间范围 [start, end]（闭区间，日期字符串 YYYY-MM-DD；缺省 = 不限）
- 统计对象：未软删的设计系统（历史事件保留但软删系统不进统计）
- 预览数 = SUM(event_type='view')；调用量 = SUM(event_type='usage')
- 使用人数 = COUNT(DISTINCT account)（匿名事件 account 为 NULL，不计入人数）
- 最近调用时间 = MAX(created_at)（任意类型事件）
- 部门维度 = 事件快照 dept1（人员转部门不影响历史统计）；缺失归「未知」

trend / users 采用「SQL 过滤 + Python 聚合」：内网规模事件量下最简单、跨库（SQLite/MySQL）
无方言问题，且周/月桶与 DISTINCT 账号的组合聚合语义正确。
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.design_system import DesignSystem
from app.models.ds_usage_event import DsUsageEvent

logger = logging.getLogger(__name__)

METRICS = ("view", "usage", "users")
GRANULARITIES = ("day", "week", "month")


def _parse_range(start: str, end: str):
    """日期字符串 → (datetime|None, datetime|None)。start 取当天 00:00:00，end 取当天 23:59:59。"""
    lo = hi = None
    if start:
        lo = datetime.strptime(str(start)[:10], "%Y-%m-%d")
    if end:
        e = datetime.strptime(str(end)[:10], "%Y-%m-%d")
        hi = e.replace(hour=23, minute=59, second=59, microsecond=0)
    return lo, hi


def _range_query(db: Session, start: str, end: str):
    lo, hi = _parse_range(start, end)
    q = db.query(DsUsageEvent)
    if lo:
        q = q.filter(DsUsageEvent.created_at >= lo)
    if hi:
        q = q.filter(DsUsageEvent.created_at <= hi)
    return q


def _views_expr():
    return func.sum(case((DsUsageEvent.event_type == "view", 1), else_=0))


def _usage_expr():
    return func.sum(case((DsUsageEvent.event_type == "usage", 1), else_=0))


def _iso(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


# ─────────────────────────── 左表：summary ───────────────────────────

def stats_summary(db: Session, start: str, end: str, search: str = "") -> dict:
    """每系统一行（无数据的系统也返回，补 0）+ 全局汇总行。

    汇总的 users 为全局 DISTINCT 账号数（同一人在多系统活动只计 1），不等于各行之和。
    软删系统的事件保留在库，但不进任何统计（行与汇总口径一致）。
    """
    # 未软删的 slug 集合：所有聚合（含全局汇总）都以它圈定事件范围
    all_slugs = [
        s for (s,) in db.query(DesignSystem.slug).filter(DesignSystem.is_deleted == 0).all()
    ]
    slug_set = set(all_slugs)

    rows_q = (
        _range_query(db, start, end)
        .with_entities(
            DsUsageEvent.slug,
            _views_expr().label("views"),
            _usage_expr().label("usage"),
            func.count(func.distinct(DsUsageEvent.account)).label("users"),
            func.max(DsUsageEvent.created_at).label("last_at"),
        )
    )
    if slug_set:
        rows_q = rows_q.filter(DsUsageEvent.slug.in_(slug_set))
    else:
        from sqlalchemy import false
        rows_q = rows_q.filter(false())
    rows = rows_q.group_by(DsUsageEvent.slug).all()
    by_slug = {r.slug: r for r in rows}

    sys_q = db.query(DesignSystem.slug, DesignSystem.name).filter(DesignSystem.is_deleted == 0)
    if search and search.strip():
        # 转义 LIKE 通配符，搜索词按字面量匹配（% _ 不再生效）
        kw = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sys_q = sys_q.filter(DesignSystem.name.ilike("%%%s%%" % kw, escape="\\"))
    systems = sys_q.order_by(DesignSystem.id).all()

    items = []
    for slug, name in systems:
        r = by_slug.get(slug)
        items.append({
            "slug": slug,
            "name": name,
            "views": int(r.views or 0) if r else 0,
            "usage": int(r.usage or 0) if r else 0,
            "users": int(r.users or 0) if r else 0,
            "last_at": _iso(r.last_at) if r else None,
        })

    total_q = _range_query(db, start, end).with_entities(
        _views_expr(), _usage_expr(),
        func.count(func.distinct(DsUsageEvent.account)),
        func.max(DsUsageEvent.created_at),
    )
    if not slug_set:
        tv, tu, tc, tl = (0, 0, 0, None)
    else:
        tv, tu, tc, tl = total_q.filter(DsUsageEvent.slug.in_(slug_set)).one()
    total = {
        "views": int(tv or 0),
        "usage": int(tu or 0),
        "users": int(tc or 0),
        "last_at": _iso(tl),
    }
    return {"start": start or None, "end": end or None, "total": total, "items": items}


# ─────────────────────────── 打点分布：trend / dept-share ───────────────────────────

def _bucket_date(dt: datetime, granularity: str):
    d = dt.date()
    if granularity == "week":
        return d - timedelta(days=d.weekday())      # 所在周的周一
    if granularity == "month":
        return d.replace(day=1)
    return d


def stats_trend(db: Session, metric: str, granularity: str, start: str, end: str) -> dict:
    """条形图：时间桶（天/周/月）× 一层部门（dept1）→ 指标值。

    返回扁平行 [{date, dept1, value}]，前端透视为堆叠柱状图（X=时间、系列=dept1）。
    users 指标按 (桶, dept1) 内 DISTINCT 账号计数（同人在同桶多天只计 1）。
    """
    agg = {}  # (bucket, dept1) -> set(account) | count
    q = _range_query(db, start, end).with_entities(
        DsUsageEvent.event_type, DsUsageEvent.account,
        DsUsageEvent.dept1, DsUsageEvent.created_at,
    )
    for ev_type, account, dept1, created_at in q:
        key = (_bucket_date(created_at, granularity), dept1 or "")
        if metric == "users":
            if account:
                agg.setdefault(key, set()).add(account)
        elif ev_type == metric:
            agg[key] = agg.get(key, 0) + 1
    buckets = [
        {"date": k[0].isoformat(), "dept1": k[1], "value": len(v) if metric == "users" else v}
        for k, v in agg.items()
    ]
    buckets.sort(key=lambda x: (x["date"], x["dept1"]))
    return {"metric": metric, "granularity": granularity,
            "start": start or None, "end": end or None, "buckets": buckets}


def stats_dept_share(db: Session, metric: str, start: str, end: str) -> dict:
    """扇形图：一层部门（dept1）占比。users 指标 = 各部门 DISTINCT 账号数。"""
    if metric == "users":
        rows = (
            _range_query(db, start, end)
            .with_entities(DsUsageEvent.dept1, func.count(func.distinct(DsUsageEvent.account)))
            .group_by(DsUsageEvent.dept1)
            .all()
        )
    else:
        expr = _views_expr() if metric == "view" else _usage_expr()
        rows = (
            _range_query(db, start, end)
            .with_entities(DsUsageEvent.dept1, expr)
            .group_by(DsUsageEvent.dept1)
            .all()
        )
    items = [{"dept1": d or "", "value": int(v or 0)} for d, v in rows]
    items = [i for i in items if i["value"] > 0]  # 0 值切片对饼图是噪音（该部门在此指标下无打点）
    items.sort(key=lambda x: -x["value"])
    return {"metric": metric, "start": start or None, "end": end or None, "items": items}


# ─────────────────────────── 人员统计：users ───────────────────────────

def stats_users(db: Session, start: str, end: str, search: str = "") -> dict:
    """人员统计表：按 account 分组。

    名字/部门取该账号**最新一条事件**的快照；预览数/调用量为范围内合计；
    最近调用时间 = 范围内最后一次事件时间。search 匹配 工号/名字（模糊）。
    """
    q = _range_query(db, start, end).with_entities(
        DsUsageEvent.account, DsUsageEvent.nick_name,
        DsUsageEvent.dept1, DsUsageEvent.dept2, DsUsageEvent.dept3, DsUsageEvent.dept4,
        DsUsageEvent.event_type, DsUsageEvent.created_at, DsUsageEvent.id,
    ).order_by(DsUsageEvent.created_at.asc(), DsUsageEvent.id.asc())

    per = {}  # account -> state
    order = []
    for account, nick, d1, d2, d3, d4, ev_type, created_at, _id in q:
        if not account:
            continue  # 匿名事件不生成人员行（统计归「未知」，人员表只列可识别账号）
        key = account
        st = per.get(key)
        if st is None:
            st = per[key] = {"account": key, "nick_name": "", "last_at": created_at,
                             "views": 0, "usage": 0, "dept": ["", "", "", ""]}
            order.append(key)
        # 最新事件的快照覆盖（查询已按时间升序，后面的覆盖前面的）
        if nick:
            st["nick_name"] = nick
        for i, d in enumerate((d1, d2, d3, d4)):
            if d:
                st["dept"][i] = d
        if ev_type == "view":
            st["views"] += 1
        elif ev_type == "usage":
            st["usage"] += 1
        st["last_at"] = created_at

    items = []
    for key in order:
        st = per[key]
        if search and search.strip():
            kw = search.strip().lower()
            if kw not in st["account"].lower() and kw not in st["nick_name"].lower():
                continue
        items.append({
            "account": st["account"],
            "nick_name": st["nick_name"],
            "last_at": _iso(st["last_at"]),
            "views": st["views"],
            "usage": st["usage"],
            "dept1": st["dept"][0], "dept2": st["dept"][1],
            "dept3": st["dept"][2], "dept4": st["dept"][3],
        })
    items.sort(key=lambda x: x["last_at"] or "", reverse=True)
    return {"start": start or None, "end": end or None, "total": len(items), "items": items}


# ─────────────────────────── 7c. 打点事件用户信息补全 ───────────────────────────

def refresh_event_identities(db: Session, accounts=None) -> dict:
    """打点事件用户信息补全（公开维护接口）：只补空，不修订已有快照。

    - 候选：account 非空且（nick_name 或 dept1 为空）的事件 → DISTINCT account；
      accounts 参数可限定范围（仍只处理其中身份不完整的事件）
    - 逐账号走 resolve 链（users 表 → getAccount 人员服务 → 回写缓存），
      查到 nick_name 或部门后**逐字段填充**——事件内已有值的字段一律不动（历史快照不修订）
    - 查不到的账号进 unresolved 名单，事件原样保留（绝不丢打点，等下次补全）
    - 匿名事件（account 为空）永不触碰；幂等：已补全的事件不再进候选
    """
    from app.services.operator import OperatorInfo
    from app.services.user_info_service import resolve_user_info, snapshot_fields

    q = (
        db.query(DsUsageEvent.account)
        .filter(
            DsUsageEvent.account.isnot(None),
            DsUsageEvent.account != "",
            or_(
                DsUsageEvent.nick_name.is_(None),
                DsUsageEvent.nick_name == "",
                DsUsageEvent.dept1.is_(None),
                DsUsageEvent.dept1 == "",
            ),
        )
        .distinct()
    )
    if accounts:
        cleaned = sorted({str(a).strip() for a in accounts if str(a).strip()})
        if not cleaned:
            return {"accounts_total": 0, "resolved": 0, "unresolved": [], "events_updated": 0}
        q = q.filter(DsUsageEvent.account.in_(cleaned))

    candidates = [row[0] for row in q.all()]
    resolved, events_updated, unresolved = 0, 0, []
    for acc in candidates:
        info = resolve_user_info(db, OperatorInfo(account=acc))
        nick = (info.get("nick_name") or "").strip()
        _, _, d1, d2, d3, d4 = snapshot_fields(info)
        fills = {"nick_name": nick, "dept1": d1, "dept2": d2, "dept3": d3, "dept4": d4}
        if not nick and not d1:
            unresolved.append(acc)
            continue
        resolved += 1
        # 只补空：逐行逐字段填充（Python 侧处理，跨库无方言问题；内网事件量级）
        touched = 0
        rows = db.query(DsUsageEvent).filter(DsUsageEvent.account == acc).all()
        for ev in rows:
            changed = False
            for col, val in fills.items():
                if val and not (getattr(ev, col) or "").strip():
                    setattr(ev, col, val)
                    changed = True
            if changed:
                touched += 1
        events_updated += touched

    db.commit()
    return {
        "accounts_total": len(candidates),
        "resolved": resolved,
        "unresolved": unresolved,
        "events_updated": events_updated,
    }
