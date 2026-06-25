from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    resource_type  = Column(SmallInteger, nullable=False, comment="1=组件集 2=模版 3=SVG 4=插画 5=图片")
    name           = Column(String(255), nullable=False)
    file_name      = Column(String(255), nullable=True, comment="文件名，如 abc.svg")
    file_path      = Column(String(500), nullable=True, comment="文件相对路径，如 icon/abc.svg")
    file_size      = Column(Integer, nullable=True, comment="文件大小（bytes）")
    mime_type      = Column(String(100), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    dimensions     = Column(JSON, nullable=True, comment='{"width": 100, "height": 100}')
    description    = Column(Text, nullable=True)
    raw_data       = Column(Text, nullable=True, comment="原始数据 JSON 字符串")
    created_by     = Column(String(100), nullable=True)
    is_deleted     = Column(Integer, nullable=False, default=0)
    sort_order     = Column(Integer, nullable=False, default=0)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")


class ResourceTag(Base):
    __tablename__ = "resource_tags"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    tag         = Column(String(100), nullable=False)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="tags")
