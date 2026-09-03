"""
搜索统计看板路由
GET    /api/search-stats?start_date=&end_date=           看板数据
POST   /api/search-stats/refresh?target_date=            聚合指定日期（不传则全量重建）
POST   /api/search-stats/import-logs                     从历史日志文件导入搜索记录
POST   /api/search-stats/migrate-illustration            将日志表 illustration 修正为 illus
DELETE /api/search-stats?resource_type=                   按资源类型删除统计汇总
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
    granularity: str = Query("month", description="柱状图统计粒度 day/week/month"),
    app_granularity: str = Query("month", description="三方占用柱状图统计粒度 day/week/month"),
    db: Session = Depends(get_db),
):
    if granularity not in {"day", "week", "month"}:
        raise HTTPException(status_code=400, detail=f"无效的 granularity: {granularity}，可选值: day/week/month")
    if app_granularity not in {"day", "week", "month"}:
        raise HTTPException(status_code=400, detail=f"无效的 app_granularity: {app_granularity}，可选值: day/week/month")
    return search_stats_service.get_dashboard_data(
        db,
        _parse_date(start_date),
        _parse_date(end_date),
        granularity=granularity,
        app_granularity=app_granularity,
    )


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


@router.post("/migrate-illustration")
def migrate_illustration(db: Session = Depends(get_db)):
    """将 vector_search_logs 中 resource_type='illustration' 的记录修正为 'illus'。

    仅修正日志主表，不重建汇总表。如需更新看板，请再调用 /refresh 全量重建。
    """
    result = search_stats_service.migrate_illustration_to_illus(db)
    return {"message": "修正完成", **result}


@router.post("/migrate-app-id")
def migrate_app_id(
    old_app_id: str = Query(..., description="旧的 app_id"),
    new_app_id: str = Query(..., description="新的 app_id"),
    db: Session = Depends(get_db),
):
    """将 vector_search_logs 中 app_id=old 的记录批量修正为 new。

    仅修正日志主表，不重建汇总表。如需更新看板，请再调用 /refresh 全量重建。
    """
    result = search_stats_service.migrate_app_id(db, old_app_id, new_app_id)
    return {"message": "修正完成", **result}


@router.delete("")
def delete_stats_by_type(
    resource_type: str = Query(..., description="要删除的资源类型，如 component/icon/illus/image/file"),
    db: Session = Depends(get_db),
):
    """按资源类型删除 search_daily_stats 汇总数据。删除后请调用 /refresh 重建。"""
    result = search_stats_service.delete_stats_by_type(db, resource_type)
    return {"message": "删除完成", **result}
