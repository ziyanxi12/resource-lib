from enum import IntEnum


class ResourceType(IntEnum):
    """
    资源六大类型枚举
    数据库存整数，API 传/返字符串，在此处做双向转换
    """
    component = 1  # 组件集
    icon      = 3  # SVG 图标
    illus     = 4  # 插画
    image     = 5  # 图片
    file      = 6  # 文件

    @classmethod
    def from_name(cls, name: str) -> "ResourceType":
        """从字符串名称获取枚举值，name 不合法时抛 KeyError"""
        return cls[name]

    @property
    def label(self) -> str:
        """返回中文展示名称"""
        _labels = {
            1: "组件集",
            3: "SVG",
            4: "插画",
            5: "图片",
            6: "文件",
        }
        return _labels[self.value]

    @property
    def vec_type(self) -> str:
        """返回向量服务集合名（illus → illustration，其余与枚举名一致）"""
        _vec_types = {
            1: "component",
            3: "icon",
            4: "illustration",
            5: "image",
            6: "file",
        }
        return _vec_types[self.value]
