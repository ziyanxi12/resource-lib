from fastapi import Request


class OperatorInfo:
    """操作人信息（8 字段），兼容旧 tuple 解包。

    旧代码 account, name = get_operator(request) 无需改动。
    新代码可直接 op = get_operator(request); op.dept
    """

    __slots__ = ("account", "dept", "deptcode", "nick_name", "role_id", "roles", "uid", "uuid")

    def __init__(
        self,
        account: str = "unknown",
        dept: str = "",
        deptcode: str = "",
        nick_name: str = "unknown",
        role_id: str = "",
        roles: str = "",
        uid: str = "",
        uuid: str = "",
    ):
        self.account = account
        self.dept = dept
        self.deptcode = deptcode
        self.nick_name = nick_name
        self.role_id = role_id
        self.roles = roles
        self.uid = uid
        self.uuid = uuid

    @property
    def name(self) -> str:
        """兼容旧字段名：name = nickName"""
        return self.nick_name

    def __iter__(self):
        """支持 account, name = get_operator(request) 的 tuple 解包"""
        yield self.account
        yield self.nick_name

    def __repr__(self):
        return f"OperatorInfo(account={self.account!r}, nick_name={self.nick_name!r})"


def get_operator(request: Request) -> OperatorInfo:
    """从 request.state 获取操作人信息（由 AuthMiddleware 解密后存入）。

    返回 OperatorInfo，兼容旧 tuple 解包：account, name = get_operator(request)
    """
    op = getattr(request.state, "operator", None)
    if op is not None:
        return op
    return OperatorInfo()
