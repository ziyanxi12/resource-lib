from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, Float, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    resource_type  = Column(SmallInteger, nullable=False, comment="1=component 2=template 3=icon 4=illus 5=image 6=file")
    name           = Column(String(255), nullable=False)
    file_name      = Column(String(255), nullable=True, comment="文件名，如 abc.svg")
    file_path      = Column(String(500), nullable=True, comment="文件相对路径，如 icon/abc.svg")
    file_size      = Column(Integer, nullable=True, comment="文件大小（bytes）")
    mime_type      = Column(String(100), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    width          = Column(Float, nullable=True, comment="资源宽度（px），可能为小数")
    height         = Column(Float, nullable=True, comment="资源高度（px），可能为小数")
    description    = Column(Text, nullable=True)
    raw_data       = Column(Text, nullable=True, comment="原始数据 JSON 字符串")
    group_id       = Column(Integer, ForeignKey("resource_groups.id", ondelete="SET NULL"), nullable=True, comment="所属分组ID")
    created_by     = Column(String(100), nullable=True)
    is_deleted     = Column(Integer, nullable=False, default=0)
    created_at         = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at         = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_updated_at    = Column(DateTime, nullable=True, comment="业务数据更新时间，用于向量同步判断")
    vector_updated_at  = Column(DateTime, nullable=True, comment="向量库更新时间")

    tags = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")
    component_variant = relationship("ComponentVariant", back_populates="resource", uselist=False)
    icon_detail       = relationship("ResourceIcon",  back_populates="resource", uselist=False)
    illus_detail      = relationship("ResourceIllus", back_populates="resource", uselist=False)
    group             = relationship("ResourceGroup", back_populates="resources")


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
    lib_file_key    = Column(String(100), nullable=True,  comment="组件库文件key")
    lib_name        = Column(String(255), nullable=True,  comment="组件库名称")
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


class ResourceGroup(Base):
    """资源分组，树形结构，每种资源类型有独立的分组树"""
    __tablename__ = "resource_groups"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(SmallInteger, nullable=False, comment="资源类型：1-6 对应六类资源")
    name          = Column(String(255), nullable=False, comment="分组名称")
    parent_id     = Column(Integer, ForeignKey("resource_groups.id", ondelete="CASCADE"), nullable=True, comment="父分组ID，NULL表示根节点")
    level         = Column(SmallInteger, default=0, comment="层级深度：0=根节点")
    real_path     = Column(String(500), nullable=False, comment="完整路径：根分组/一级分组/二级分组")
    sort_order    = Column(Integer, default=0, comment="同级排序序号")
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    children  = relationship("ResourceGroup", backref="parent", remote_side=[id], cascade="all")
    resources = relationship("Resource", back_populates="group")
