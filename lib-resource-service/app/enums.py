from enum import IntEnum


class ResourceType(IntEnum):
    """
    资源五大类型枚举
    数据库存整数，API 传/返字符串，在此处做双向转换
    """
    component_set = 1  # 组件集
    template      = 2  # 模版
    svg           = 3  # SVG
    illustration  = 4  # 插画
    image         = 5  # 图片

    @classmethod
    def from_name(cls, name: str) -> "ResourceType":
        """从字符串名称获取枚举值，name 不合法时抛 KeyError"""
        return cls[name]

    @property
    def label(self) -> str:
        """返回中文展示名称"""
        _labels = {
            1: "组件集",
            2: "模版",
            3: "SVG",
            4: "插画",
            5: "图片",
        }
        return _labels[self.value]
