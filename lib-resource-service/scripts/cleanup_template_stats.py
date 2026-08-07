"""
清理历史遗留的 template 搜索统计。

背景：旧版系统支持 template 资源类型（枚举 ID=2），已在 enums.py 中移除，
但 vector_search_logs 与 search_daily_stats 仍残留历史 template 数据。
本脚本将其彻底删除，避免看板出现无对应资源类型的统计项。

用法：
    cd lib-resource-service && python3 scripts/cleanup_template_stats.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.search_log import VectorSearchLog
from app.models.search_log_result import SearchLogResult
from app.models.search_daily_stats import SearchDailyStats

if __name__ == "__main__":
    db = SessionLocal()
    try:
        log_ids = [
            r[0] for r in db.query(VectorSearchLog.id)
            .filter(VectorSearchLog.resource_type == "template")
            .all()
        ]

        results_deleted = 0
        logs_deleted = 0
        if log_ids:
            results_deleted = db.query(SearchLogResult) \
                .filter(SearchLogResult.log_id.in_(log_ids)) \
                .delete(synchronize_session=False)
            logs_deleted = db.query(VectorSearchLog) \
                .filter(VectorSearchLog.id.in_(log_ids)) \
                .delete(synchronize_session=False)

        stats_deleted = db.query(SearchDailyStats) \
            .filter(SearchDailyStats.resource_type == "template") \
            .delete(synchronize_session=False)

        db.commit()
        print(f"删除 template 源日志: {logs_deleted} 条 (id={log_ids})")
        print(f"删除关联结果子表行: {results_deleted} 条")
        print(f"删除汇总表 template 行: {stats_deleted} 条")
    finally:
        db.close()
