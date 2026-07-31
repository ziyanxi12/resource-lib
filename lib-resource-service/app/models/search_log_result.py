from sqlalchemy import Column, Integer, Float, ForeignKey
from app.database import Base


class SearchLogResult(Base):
    """搜索日志命中结果子表 — 每个命中资源一行（多 query 命中取最高分），用于统计资源命中频次"""

    __tablename__ = "search_log_results"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    log_id      = Column(Integer, ForeignKey("vector_search_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, nullable=False, index=True)
    score       = Column(Float, nullable=True, comment="该资源的最高相关性分数（多 query 命中取最高）")
