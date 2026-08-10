from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, String, Text, DateTime, Index
from app.database import Base


class OperationLog(Base):
    """操作日志表，记录前端用户的所有写操作"""
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("idx_op_logs_source_id", "source_id"),
        Index("idx_op_logs_created_at", "created_at"),
    )

    id               = Column(Integer, primary_key=True, autoincrement=True)
    source_id        = Column(Integer, nullable=True, comment="关联来源ID")
    resource_type    = Column(SmallInteger, nullable=True, comment="资源类型 1/3/4/5/6")
    operator         = Column(String(100), nullable=False, comment="操作人昵称")
    operator_account = Column(String(100), nullable=False, comment="操作人账号")
    action           = Column(String(50), nullable=False, comment="操作类型：create/update/delete/batch_delete/batch_clear/batch_move/batch_upload/batch_import/batch_import_cancel/move/restore/vector_sync/ai_understand")
    target_type      = Column(String(30), nullable=False, comment="对象类型：resource/group/source")
    target_id        = Column(Integer, nullable=True, comment="对象ID")
    target_name      = Column(String(255), nullable=True, comment="对象名称")
    detail           = Column(Text, nullable=True, comment="变更详情 JSON 字符串")
    created_at       = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")
