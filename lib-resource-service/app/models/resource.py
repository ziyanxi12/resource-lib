from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    resource_type  = Column(SmallInteger, nullable=False, comment="1=component 2=template 3=icon 4=illus 5=image")
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
    component_variant = relationship("ComponentVariant", back_populates="resource", uselist=False)
    icon_detail       = relationship("ResourceIcon",  back_populates="resource", uselist=False)
    illus_detail      = relationship("ResourceIllus", back_populates="resource", uselist=False)


class ResourceTag(Base):
    __tablename__ = "resource_tags"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    tag         = Column(String(100), nullable=False)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="tags")


class ComponentVariant(Base):
    """组件变体详情，通过 resource_id 关联主表，parent_key 用于分组查询同一组件集的所有变体"""
    __tablename__ = "component_variants"

    variant_key     = Column(String(100), primary_key=True, comment="变体 key，来自 Figma，全局唯一")
    resource_id     = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, unique=True)
    domain          = Column(String(255), nullable=True,  comment="所属域，如 ICT_UI")
    canvas_name     = Column(String(255), nullable=True,  comment="画布分组名，如 '1.基础类'")
    component_name  = Column(String(255), nullable=True,  comment="组件集名称")
    component_guid  = Column(String(100), nullable=True,  comment="组件集 guid")
    component_key   = Column(String(100), nullable=True,  comment="组件集 key，即 parentKey")
    name            = Column(String(500), nullable=False, comment="变体属性字符串")
    guid            = Column(String(100), nullable=True,  unique=True)
    component_props = Column(JSON, nullable=True,         comment="[{name, type}, ...]")
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at      = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("Resource", back_populates="component_variant")


class ResourceIcon(Base):
    """SVG 图标结构化详情，通过 resource_id 关联主表"""
    __tablename__ = "resource_icons"

    icon_id      = Column(String(100), primary_key=True, comment="图标原始 id（来自 JSON 数据）")
    resource_id  = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, unique=True)
    chinese_name = Column(String(255), nullable=True, comment="中文名称")
    name         = Column(String(255), nullable=True, comment="英文全称，如 it_home")
    english_name = Column(String(255), nullable=True, comment="英文短名，如 home")
    category     = Column(String(100), nullable=True)
    group        = Column(String(100), nullable=True, comment="领域")
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("Resource", back_populates="icon_detail")


class ResourceIllus(Base):
    """插画结构化详情，通过 resource_id 关联主表"""
    __tablename__ = "resource_illus"

    illus_id    = Column(String(100), primary_key=True, comment="插画原始 id（来自 JSON 数据）")
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, unique=True)
    category    = Column(String(100), nullable=True)
    tags        = Column(JSON, nullable=True, comment="标签列表，如 [\"空状态\", \"反馈\"]")
    version     = Column(String(50), nullable=True)
    theme       = Column(String(100), nullable=True)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("Resource", back_populates="illus_detail")
