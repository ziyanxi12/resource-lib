"""
搜索统计服务 — 从 vector_search_logs 聚合到 search_daily_stats，看板数据查询，历史日志导入。
"""
import ast
import glob
import logging
import os
import re
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import _is_sqlite
from app.models.search_daily_stats import SearchDailyStats
from app.models.search_log import VectorSearchLog
from app.models.search_log_result import SearchLogResult
from app.models.search_app import SearchApp

logger = logging.getLogger(__name__)


def refresh_daily_stats(db: Session, target_date) -> dict:
    """聚合指定日期的搜索日志，写入 search_daily_stats（先删后插）。"""
    date_str = target_date.isoformat() if hasattr(target_date, "isoformat") else str(target_date)

    date_expr = func.date(VectorSearchLog.created_at)

    rows = (
        db.query(
            VectorSearchLog.app_id,
            VectorSearchLog.resource_type,
            func.count().label("api_call_count"),
            func.coalesce(func.sum(VectorSearchLog.result_count), 0).label("resource_return_count"),
        )
        .filter(
            date_expr == date_str,
            VectorSearchLog.status == "success",
        )
        .group_by(VectorSearchLog.app_id, VectorSearchLog.resource_type)
        .all()
    )

    apps_map = {}
    if rows:
        app_ids = [r.app_id for r in rows if r.app_id]
        if app_ids:
            app_rows = db.query(SearchApp).filter(SearchApp.app_id.in_(app_ids)).all()
            apps_map = {a.app_id: a.name for a in app_rows}

    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    db.query(SearchDailyStats).filter(SearchDailyStats.stat_date == target_date).delete()
    db.flush()

    created = 0
    for r in rows:
        app_id = r.app_id
        if app_id is None:
            app_name = "匿名调用"
        elif app_id in apps_map:
            app_name = apps_map[app_id]
        else:
            app_name = "未注册应用"

        stat = SearchDailyStats(
            stat_date=target_date,
            app_id=app_id,
            app_name=app_name,
            resource_type=r.resource_type or "unknown",
            api_call_count=r.api_call_count,
            resource_return_count=int(r.resource_return_count),
        )
        db.add(stat)
        created += 1

    db.commit()
    logger.info("聚合完成: date=%s, rows=%d", target_date, created)
    return {"date": target_date.isoformat(), "rows": created}


def refresh_all_stats(db: Session) -> dict:
    """全量重建：先清空汇总表，再遍历 vector_search_logs 中所有日期逐天聚合。"""
    db.query(SearchDailyStats).delete()
    db.flush()

    date_col = func.date(VectorSearchLog.created_at)

    dates = (
        db.query(date_col.distinct().label("d"))
        .filter(VectorSearchLog.status == "success")
        .all()
    )

    total_rows = 0
    for (d,) in dates:
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        elif isinstance(d, datetime):
            d = d.date()
        result = refresh_daily_stats(db, d)
        total_rows += result["rows"]

    return {"dates": len(dates), "rows": total_rows}


def _get_last_updated(db: Session) -> Optional[int]:
    """返回全表最后一次聚合更新时间（epoch 秒），不受日期范围过滤。"""
    last_updated = db.query(func.max(SearchDailyStats.updated_at)).scalar()
    if last_updated is None:
        return None
    if isinstance(last_updated, datetime):
        return int(last_updated.timestamp() * 1000)
    return int(last_updated)


def get_dashboard_data(db: Session, start_date, end_date, granularity: str = "month") -> dict:
    """一次返回看板所需的全部统计数据。

    granularity: 柱状图统计粒度，day/week/month。
    """
    if granularity not in {"day", "week", "month"}:
        raise ValueError(f"无效的 granularity: {granularity}，可选值: day/week/month")

    # 1. 汇总数字
    summary_row = (
        db.query(
            func.coalesce(func.sum(SearchDailyStats.api_call_count), 0).label("api_call_count"),
            func.coalesce(func.sum(SearchDailyStats.resource_return_count), 0).label("resource_return_count"),
        )
        .filter(
            SearchDailyStats.stat_date >= start_date,
            SearchDailyStats.stat_date <= end_date,
        )
        .first()
    )

    summary = {
        "api_call_count": int(summary_row.api_call_count) if summary_row else 0,
        "resource_return_count": int(summary_row.resource_return_count) if summary_row else 0,
    }

    # 2. 饼图：按资源类型
    pie_rows = (
        db.query(
            SearchDailyStats.resource_type,
            func.coalesce(func.sum(SearchDailyStats.api_call_count), 0).label("api_call_count"),
            func.coalesce(func.sum(SearchDailyStats.resource_return_count), 0).label("resource_return_count"),
        )
        .filter(
            SearchDailyStats.stat_date >= start_date,
            SearchDailyStats.stat_date <= end_date,
        )
        .group_by(SearchDailyStats.resource_type)
        .all()
    )
    pie = [
        {
            "resource_type": r.resource_type,
            "api_call_count": int(r.api_call_count),
            "resource_return_count": int(r.resource_return_count),
        }
        for r in pie_rows
    ]

    # 3. 柱状图：按资源类型 + 统计粒度（天/周/月）
    if granularity == "day":
        if _is_sqlite:
            period_expr = func.strftime("%Y-%m-%d", SearchDailyStats.stat_date)
        else:
            period_expr = func.date_format(SearchDailyStats.stat_date, "%Y-%m-%d")
    elif granularity == "week":
        if _is_sqlite:
            # 取本周周一日期作为分组标签，跨年排序也正确
            period_expr = func.strftime("%Y-%m-%d", SearchDailyStats.stat_date, "weekday 1", "-7 days")
        else:
            period_expr = func.date_format(
                func.date_sub(SearchDailyStats.stat_date, text("interval weekday(stat_date) day")),
                "%Y-%m-%d",
            )
    else:
        if _is_sqlite:
            period_expr = func.strftime("%Y-%m", SearchDailyStats.stat_date)
        else:
            period_expr = func.date_format(SearchDailyStats.stat_date, "%Y-%m")

    bar_rows = (
        db.query(
            SearchDailyStats.resource_type,
            period_expr.label("period"),
            func.coalesce(func.sum(SearchDailyStats.api_call_count), 0).label("api_call_count"),
            func.coalesce(func.sum(SearchDailyStats.resource_return_count), 0).label("resource_return_count"),
        )
        .filter(
            SearchDailyStats.stat_date >= start_date,
            SearchDailyStats.stat_date <= end_date,
        )
        .group_by(SearchDailyStats.resource_type, period_expr)
        .all()
    )
    bar = [
        {
            "resource_type": r.resource_type,
            "period": r.period,
            "api_call_count": int(r.api_call_count),
            "resource_return_count": int(r.resource_return_count),
        }
        for r in bar_rows
    ]

    # 4. 三方调用详情：按 app + 资源类型
    app_rows = (
        db.query(
            SearchDailyStats.app_id,
            SearchDailyStats.app_name,
            SearchDailyStats.resource_type,
            func.coalesce(func.sum(SearchDailyStats.api_call_count), 0).label("api_call_count"),
            func.coalesce(func.sum(SearchDailyStats.resource_return_count), 0).label("resource_return_count"),
        )
        .filter(
            SearchDailyStats.stat_date >= start_date,
            SearchDailyStats.stat_date <= end_date,
        )
        .group_by(SearchDailyStats.app_id, SearchDailyStats.app_name, SearchDailyStats.resource_type)
        .order_by(func.sum(SearchDailyStats.api_call_count).desc())
        .all()
    )
    apps = [
        {
            "app_id": r.app_id,
            "app_name": r.app_name or "匿名调用",
            "resource_type": r.resource_type,
            "api_call_count": int(r.api_call_count),
            "resource_return_count": int(r.resource_return_count),
        }
        for r in app_rows
    ]

    return {
        "summary": summary,
        "pie": pie,
        "bar": bar,
        "apps": apps,
        "last_updated": _get_last_updated(db),
    }


# ── 历史日志导入 ──────────────────────────────────────────────

_PATTERN_SEARCH = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\].*"
    r"\[batch_search(?:_async)?\] 发起批量搜索: type=(\S+)\s+queries=(\[.*?\])\s+mode=(\S+)\s+top_k=(\d+)"
)
_PATTERN_RETURN_HIT = re.compile(
    r"\[batch_search(?:_async)?\] 返回 (\d+) 组结果: 第1组\((\d+)条\)前3条=(\[.*?\])"
)
_PATTERN_RETURN_EMPTY = re.compile(
    r"\[batch_search(?:_async)?\] 返回 0 组结果"
)
_PATTERN_FAIL = re.compile(
    r"\[batch_search(?:_async)?\] 批量搜索失败: (\S+), type=(\S+),"
)


def _normalize_rtype(rtype: str) -> str:
    """归一化资源类型：历史日志中的 illustration 统一为 illus。"""
    if rtype == "illustration":
        return "illus"
    return rtype


def _parse_queries(queries_str: str) -> list:
    try:
        parsed = ast.literal_eval(queries_str)
        if isinstance(parsed, list):
            return [str(q) for q in parsed]
    except Exception:
        pass
    return []


def _parse_results_prefix(results_str: str) -> list:
    items = []
    try:
        parsed = ast.literal_eval(results_str)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "data_id" in item:
                    data_id = str(item["data_id"])
                    score = item.get("score")
                    if data_id.isdigit():
                        items.append({"resource_id": int(data_id), "score": float(score) if score else None})
    except Exception:
        pass
    return items


def _process_log_file(filepath: str) -> list:
    records = []
    pending = None

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _PATTERN_SEARCH.search(line)
            if m:
                if pending:
                    pending["status"] = "error"
                    pending["error_message"] = "未找到返回行"
                    records.append(pending)

                ts_str, rtype, queries_str, mode, top_k = m.groups()
                parsed_queries = _parse_queries(queries_str)
                pending = {
                    "created_at": datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S"),
                    "resource_type": rtype,
                    "queries": parsed_queries,
                    "query_count": len(parsed_queries),
                    "search_mode": mode,
                    "top_k": int(top_k),
                    "result_count": None,
                    "result_items": [],
                    "status": "success",
                    "http_status": 200,
                    "error_message": None,
                }
                continue

            if pending is None:
                continue

            m = _PATTERN_RETURN_HIT.search(line)
            if m:
                group_count, first_group_count, results_str = m.groups()
                pending["result_count"] = int(first_group_count)
                pending["result_items"] = _parse_results_prefix(results_str)
                records.append(pending)
                pending = None
                continue

            m = _PATTERN_RETURN_EMPTY.search(line)
            if m:
                pending["result_count"] = 0
                records.append(pending)
                pending = None
                continue

            m = _PATTERN_FAIL.search(line)
            if m:
                error_type, fail_type = m.groups()
                if fail_type == pending["resource_type"]:
                    pending["status"] = "error"
                    pending["http_status"] = 502
                    pending["error_message"] = error_type
                    pending["result_count"] = 0
                    records.append(pending)
                    pending = None
                continue

    if pending:
        pending["status"] = "error"
        pending["error_message"] = "未找到返回行"
        records.append(pending)

    return records


def import_logs_to_db(db: Session, logs_dir: str = None) -> dict:
    """扫描历史日志文件，解析搜索请求写入采集表。"""
    if logs_dir is None:
        from app.config import settings
        logs_dir = settings.LOG_DIR

    log_files = sorted(glob.glob(os.path.join(logs_dir, "app*.txt")))

    all_records = []
    file_stats = []
    for filepath in log_files:
        records = _process_log_file(filepath)
        if records:
            file_stats.append({"file": os.path.basename(filepath), "count": len(records)})
        all_records.extend(records)

    success = sum(1 for r in all_records if r["status"] == "success")
    error = sum(1 for r in all_records if r["status"] == "error")

    main_count = 0
    result_count = 0

    for r in all_records:
        log = VectorSearchLog(
            request_id=str(uuid.uuid4()),
            api_path="/api/vector/search",
            resource_type=_normalize_rtype(r["resource_type"]),
            search_mode=r["search_mode"],
            response_mode=None,
            top_k=r["top_k"],
            hybrid_weight=None,
            query_count=r["query_count"],
            queries=r["queries"],
            filters=None,
            result_count=r["result_count"] if r["result_count"] is not None else 0,
            status=r["status"],
            http_status=r["http_status"],
            error_message=r["error_message"],
            duration_ms=0,
            client_ip=None,
            app_id=None,
            user_agent=None,
            referer=None,
            created_at=r["created_at"],
        )
        db.add(log)
        db.flush()

        for item in r["result_items"]:
            db.add(SearchLogResult(
                log_id=log.id,
                resource_id=item["resource_id"],
                score=item["score"],
            ))
            result_count += 1

        main_count += 1

    db.commit()
    logger.info("历史日志导入完成: %d 条主表, %d 条结果子表", main_count, result_count)

    return {
        "files_scanned": len(log_files),
        "total_requests": len(all_records),
        "success": success,
        "error": error,
        "main_inserted": main_count,
        "results_inserted": result_count,
        "file_details": file_stats,
    }


def migrate_illustration_to_illus(db: Session) -> dict:
    """将 vector_search_logs 中 resource_type='illustration' 的记录修正为 'illus'。

    仅修正日志主表，不重建汇总表（如需更新看板，请手动调用 refresh_all_stats）。
    """
    updated = (
        db.query(VectorSearchLog)
        .filter(VectorSearchLog.resource_type == "illustration")
        .update({VectorSearchLog.resource_type: "illus"}, synchronize_session=False)
    )
    db.commit()
    logger.info("修正 vector_search_logs illustration -> illus: %d 条", updated)
    return {"logs_updated": int(updated)}
