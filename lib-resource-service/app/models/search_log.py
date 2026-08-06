from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, JSON, DateTime
from app.database import Base


class VectorSearchLog(Base):
    """向量搜索日志表 — 记录每次 POST /api/vector/search 请求的详细信息"""

    __tablename__ = "vector_search_logs"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    request_id    = Column(String(64), index=True, comment="请求唯一标识 uuid4")
    api_path      = Column(String(50), comment="接口路径")
    resource_type = Column(String(20), index=True, comment="资源类型 component/icon/illus/image/file")
    search_mode   = Column(String(20), nullable=True, comment="搜索模式 vector/hybrid/fulltext/dense/sparse")
    response_mode = Column(String(20), nullable=True, comment="响应模式 basic/normal/complete")
    top_k         = Column(Integer, nullable=True)
    hybrid_weight = Column(Float, nullable=True)
    query_count   = Column(Integer, nullable=True, comment="查询词数量")
    queries       = Column(JSON, nullable=True, comment="原始查询词数组")
    filters       = Column(JSON, nullable=True, comment="原始完整过滤条件（记录留存，统计走子表）")
    result_count  = Column(Integer, nullable=True, comment="去重后命中资源数")
    status        = Column(String(10), index=True, comment="success / error")
    http_status   = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms   = Column(Integer, index=True, comment="请求耗时（毫秒）")
    client_ip     = Column(String(50), index=True)
    app_id        = Column(String(50), index=True, comment="octo-vs-token 请求头，缺省回退 client_ip")
    user_agent    = Column(String(500), nullable=True)
    referer       = Column(String(500), nullable=True)
    business_data = Column(Text, nullable=True, comment="业务数据 JSON 字符串")
    created_at    = Column(DateTime, index=True, default=datetime.now)
