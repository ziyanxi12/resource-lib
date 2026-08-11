from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, JSON
from app.database import Base


class User(Base):
    """用户表，每次请求时从加密 header 解密后 upsert"""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_account", "account", unique=True),
    )

    id            = Column(Integer, primary_key=True, autoincrement=True)
    account       = Column(String(100), nullable=False, unique=True, comment="登录账号")
    dept          = Column(JSON, nullable=True, comment="部门（数组，最多4个）")
    dept_code     = Column(JSON, nullable=True, comment="部门编码（数组，最多4个）")
    nick_name     = Column(String(100), nullable=True, comment="昵称")
    role_id       = Column(String(50), nullable=True, comment="角色ID")
    roles         = Column(JSON, nullable=True, comment="角色列表（数组）")
    uid           = Column(Integer, nullable=True, comment="用户UID（数字）")
    user_id       = Column(String(100), nullable=True, comment="用户UserID")
    last_login_at = Column(DateTime, nullable=True, comment="最后活跃时间")
    created_at    = Column(DateTime, nullable=False, default=datetime.now)
    updated_at    = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
