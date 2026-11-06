"""设计系统打点事件（统计页数据源）

预览/调用发生时各写一行（与 design_systems.views / usage 列自增同事务），
人员信息（account/nick_name/dept1..4）在写入时快照——历史统计不受人员转部门影响。
统计页所有指标（预览数/调用量/使用人数/最近调用时间/部门分布）均由本表聚合派生。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String

from app.database import Base


class DsUsageEvent(Base):
    __tablename__ = "ds_usage_events"
    __table_args__ = (
        Index("idx_dsue_slug_type_time", "slug", "event_type", "created_at"),
        Index("idx_dsue_account_time", "account", "created_at"),
        Index("idx_dsue_time", "created_at"),
        Index("idx_dsue_dept1_time", "dept1", "created_at"),
    )

    id         = Column(Integer, primary_key=True, autoincrement=True)
    slug       = Column(String(100), nullable=False, comment="设计系统 slug（软删系统的历史事件保留）")
    event_type = Column(String(10), nullable=False, comment="view=预览 / usage=调用")
    account    = Column(String(100), nullable=True, comment="工号（匿名调用时为空，统计归「未知」）")
    nick_name  = Column(String(100), nullable=True, comment="快照：名字")
    dept1      = Column(String(255), nullable=True, comment="快照：一层部门")
    dept2      = Column(String(255), nullable=True, comment="快照：二层部门")
    dept3      = Column(String(255), nullable=True, comment="快照：三层部门")
    dept4      = Column(String(255), nullable=True, comment="快照：四层部门")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="打点时间")
