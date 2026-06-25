from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    """
    资源主表，统一存储五大类资源的公共字段。
    resource_type 区分类型（见 enums.ResourceType），各类型的可选字段为 NULL。
    """
    __tablename__ = "resources"

    id             = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键，全局唯一")
    resource_type  = Column(SmallInteger, nullable=False, comment="1=组件集 2=模版 3=SVG 4=插画 5=图片")
    name           = Column(String(255), nullable=False, comment="资源名称")
    unique_key     = Column(String(255), nullable=False, unique=True, comment="唯一标识，见设计文档")
    file_path      = Column(String(500), nullable=True, comment="文件相对路径（相对于 FILE_ROOT_DIR）")
    thumbnail_path = Column(String(500), nullable=True, comment="缩略图相对路径")
    file_size      = Column(Integer, nullable=True, comment="文件大小（bytes）")
    mime_type      = Column(String(100), nullable=True, comment="MIME 类型，如 image/png")
    dimensions     = Column(JSON, nullable=True, comment='尺寸，如 {"width": 1920, "height": 1080}')
    description    = Column(Text, nullable=True, comment="描述，所有类型均可填写")
    english_name   = Column(String(255), nullable=True, comment="英文名称，svg/插画/图片使用")
    domain         = Column(String(100), nullable=True, comment="领域，仅组件集使用")
    created_by     = Column(String(100), nullable=True, comment="创建人")
    is_deleted     = Column(Integer, nullable=False, default=0, comment="软删除：0=正常 1=已删除")
    sort_order     = Column(Integer, nullable=False, default=0, comment="排序权重，越大越靠前")
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")


class ResourceTag(Base):
    """资源标签表，多对多（一个资源可打多个标签）"""
    __tablename__ = "resource_tags"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    tag         = Column(String(100), nullable=False, comment="标签名")
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="tags")
