from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class SearchApp(Base):
    """搜索应用表，管理调用向量搜索的 appId（用于日志统计区分来源）"""

    __tablename__ = "search_apps"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    app_id      = Column(String(64), unique=True, index=True, comment="系统生成，octo_vs_ + 32位hex，不可修改")
    name        = Column(String(255), nullable=False, comment="应用名称")
    remark      = Column(Text, nullable=True, comment="备注")
    is_active   = Column(Integer, default=1, comment="1=启用 0=禁用(软删除)")
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
