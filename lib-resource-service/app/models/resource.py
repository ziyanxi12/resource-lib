from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, Float, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    resource_type   = Column(SmallInteger, nullable=False, comment="1=component 2=template 3=icon 4=illus 5=image 6=file")
    source_id       = Column(Integer, ForeignKey("resource_sources.id", ondelete="RESTRICT"), nullable=False, comment="来源ID")
    name            = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    search_text     = Column(Text, nullable=True, comment="业务搜索关键词")
    vector_text     = Column(Text, nullable=True, comment="向量文本（四个字段拼接）")
    file_name       = Column(String(255), nullable=True, comment="文件名，如 abc.svg")
    file_url        = Column(String(500), nullable=True, comment="文件链接（外部）")
    file_path       = Column(String(500), nullable=True, comment="文件相对路径，如 icon/abc.svg")
    file_size       = Column(Integer, nullable=True, comment="文件大小（bytes）")
    file_type       = Column(String(50), nullable=True, comment="文件类型")
    width           = Column(Float, nullable=True, comment="资源宽度（px），可能为小数")
    height          = Column(Float, nullable=True, comment="资源高度（px），可能为小数")
    thumbnail_path  = Column(String(500), nullable=True)
    raw_data        = Column(JSON, nullable=True, comment="原始数据 JSON")
    group_id        = Column(Integer, ForeignKey("resource_groups.id", ondelete="SET NULL"), nullable=True, comment="所属分组ID")
    created_by      = Column(String(100), nullable=True)
    is_deleted      = Column(Integer, nullable=False, default=0)
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at      = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_updated_at = Column(DateTime, nullable=True, comment="业务数据更新时间，用于向量同步判断")
    vector_updated_at = Column(DateTime, nullable=True, comment="向量库更新时间")

    tags   = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")
    group  = relationship("ResourceGroup", back_populates="resources")
    source = relationship("ResourceSource", back_populates="resources")


class ResourceTag(Base):
    __tablename__ = "resource_tags"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    tag         = Column(String(100), nullable=False)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="tags")


class ResourceSource(Base):
    """资源来源表，管理数据来源（手动上传、API 同步等）"""
    __tablename__ = "resource_sources"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String(255), nullable=False, comment="来源名称")
    resource_type  = Column(SmallInteger, nullable=False, comment="关联资源类型")
    is_sync_source = Column(Integer, default=0, comment="是否同步来源")
    config         = Column(JSON, nullable=True, comment="来源配置（API 地址、认证信息等）")
    is_active      = Column(Integer, default=1, comment="是否启用")
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    resources = relationship("Resource", back_populates="source")


class ResourceGroup(Base):
    """资源分组，树形结构，每种资源类型+来源有独立的分组树"""
    __tablename__ = "resource_groups"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(SmallInteger, nullable=False, comment="资源类型：1-6 对应六类资源")
    source_id     = Column(Integer, ForeignKey("resource_sources.id", ondelete="CASCADE"), nullable=True, comment="来源ID（分组按来源独立）")
    name          = Column(String(255), nullable=False, comment="分组名称")
    parent_id     = Column(Integer, ForeignKey("resource_groups.id", ondelete="CASCADE"), nullable=True, comment="父分组ID，NULL表示根节点")
    level         = Column(SmallInteger, default=0, comment="层级深度：0=根节点")
    real_path     = Column(String(500), nullable=False, comment="完整路径：根分组/一级分组/二级分组")
    sort_order    = Column(Integer, default=0, comment="同级排序序号")
    is_default    = Column(Integer, default=0, comment="是否默认分组")
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    children  = relationship("ResourceGroup", backref="parent", remote_side=[id], cascade="all")
    resources = relationship("Resource", back_populates="group")
