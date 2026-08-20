from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class WhitelistAccount(Base):
    """访问白名单表，管理可访问本系统的账号（后端统一控制）"""

    __tablename__ = "whitelist_accounts"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    account     = Column(String(100), unique=True, index=True, comment="登录账号")
    nick_name   = Column(String(100), nullable=True, comment="昵称（展示用）")
    remark      = Column(Text, nullable=True, comment="备注")
    is_active   = Column(Integer, default=1, comment="1=启用 0=禁用(软删除)")
    created_at  = Column(DateTime, default=datetime.now)
    updated_at  = Column(DateTime, default=datetime.now, onupdate=datetime.now)