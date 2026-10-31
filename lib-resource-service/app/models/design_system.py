"""设计系统（design-system.json 上传物）

JSON 内容存文件系统（FILE_ROOT_DIR/design-systems/{slug}/design-system.json），
本表只存卡片 meta + 文件指针，与 resources 表的资源体系并行（专用模块）。
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text

from app.database import Base


class DesignSystem(Base):
    __tablename__ = "design_systems"
    __table_args__ = (
        Index("idx_design_systems_deleted", "is_deleted"),
    )

    id         = Column(Integer, primary_key=True, autoincrement=True)
    slug       = Column(String(100), nullable=False, unique=True, comment="系统标识 = JSON 的 id，对外统一使用")
    name       = Column(String(255), nullable=False, comment="卡片名称")
    desc       = Column(Text, nullable=True, comment="卡片描述")
    author     = Column(String(100), nullable=True, comment="作者")
    usage      = Column(Integer, nullable=False, default=0, comment="调用量")
    cover      = Column(String(100), nullable=True, comment="内置封面文件名")
    is_default = Column(Boolean, nullable=False, default=False, comment="默认系统，全局至多一个")
    file_path  = Column(String(500), nullable=False, comment="JSON 文件相对 FILE_ROOT_DIR 的路径")
    file_size  = Column(Integer, nullable=True, comment="JSON 文件大小（bytes）")
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0, comment="软删：1=已删除")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
