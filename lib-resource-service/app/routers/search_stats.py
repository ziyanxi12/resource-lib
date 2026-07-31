"""
搜索统计看板路由
GET  /api/search-stats?start_date=&end_date=   看板数据
POST /api/search-stats/refresh?target_date=    聚合指定日期（不传则全量重建）
POST /api/search-stats/import-logs             从历史日志文件导入搜索记录
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import search_stats_service

router = APIRouter(prefix="/api/search-stats", tags=["搜索统计"])


def _parse_date(s: str) -> date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {s}，应为 YYYY-MM-DD")


@router.get("")
def get_stats(
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return search_stats_service.get_dashboard_data(db, _parse_date(start_date), _parse_date(end_date))


@router.post("/refresh")
def refresh_stats(
    target_date: Optional[str] = Query(None, description="指定日期 YYYY-MM-DD，不传则全量重建"),
    db: Session = Depends(get_db),
):
    if target_date:
        result = search_stats_service.refresh_daily_stats(db, _parse_date(target_date))
    else:
        result = search_stats_service.refresh_all_stats(db)
    return {"message": "刷新完成", **result}


@router.post("/import-logs")
def import_logs(db: Session = Depends(get_db)):
    """从历史日志文件导入搜索调用记录到采集表。导入前请先清空采集表。"""
    result = search_stats_service.import_logs_to_db(db)
    return {"message": "导入完成", **result}
