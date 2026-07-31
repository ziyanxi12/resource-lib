from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from app.database import Base


class SearchDailyStats(Base):
    """搜索调用日汇总表 — 按 (日期, app_id, resource_type) 粒度预聚合，供看板查询"""

    __tablename__ = "search_daily_stats"
    __table_args__ = (
        UniqueConstraint("stat_date", "app_id", "resource_type", name="uq_daily_app_type"),
    )

    id                     = Column(Integer, primary_key=True, autoincrement=True)
    stat_date              = Column(Date, nullable=False, index=True, comment="统计日期")
    app_id                 = Column(String(64), nullable=True, index=True, comment="搜索应用ID，NULL=匿名调用")
    app_name               = Column(String(255), nullable=True, comment="应用名称快照")
    resource_type          = Column(String(20), nullable=False, index=True, comment="资源类型 component/icon/illus/image/file")
    api_call_count         = Column(Integer, default=0, comment="接口调用次数")
    resource_return_count  = Column(Integer, default=0, comment="资源返回数")
    created_at             = Column(DateTime, default=datetime.utcnow)
    updated_at             = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
