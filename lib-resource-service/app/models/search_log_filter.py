from sqlalchemy import Column, Integer, String, ForeignKey, Index
from app.database import Base


class SearchLogFilter(Base):
    """搜索日志筛选条件子表 — 每个 source_id/group_id/tags 值拆成一行，用于 SQL 聚合统计"""

    __tablename__ = "search_log_filters"
    __table_args__ = (Index("idx_filter_type_value", "filter_type", "filter_value"),)

    id           = Column(Integer, primary_key=True, autoincrement=True)
    log_id       = Column(Integer, ForeignKey("vector_search_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    filter_type  = Column(String(30), nullable=False, comment="source_id / group_id / tags（与原始 filters JSON key 一致）")
    filter_value = Column(String(255), nullable=False)
