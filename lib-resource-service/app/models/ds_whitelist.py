"""设计系统管理台专属白名单（与 lib-resource 原白名单完全隔离）

独立于 whitelist_accounts 表：账号、开关互不影响。
- 给设计系统加管理员，不会获得 lib-resource-ui 的访问权，反之亦然
- 开关 DS_WHITELIST_ENABLED（默认 true）只作用于设计系统模块的 check 接口
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class DsWhitelistAccount(Base):
    __tablename__ = "ds_whitelist_accounts"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    account    = Column(String(100), unique=True, index=True, comment="登录账号")
    nick_name  = Column(String(100), nullable=True, comment="昵称（展示用）")
    remark     = Column(Text, nullable=True, comment="备注")
    role       = Column(String(20), default="admin", comment="super=超管 admin=管理员")
    is_active  = Column(Integer, default=1, comment="1=启用 0=禁用(软删除)")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
