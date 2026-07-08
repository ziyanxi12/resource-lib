"""
图片语义理解模块（占位）
======================================================
此文件由图片理解模块的提供方用真实实现整体替换。

约定接口：
    understand_image(image_path: str) -> str
    - image_path: 图片文件的绝对路径
    - 返回: 图片的中文语义描述文本
    - 失败时抛出异常，由上层统一捕获处理
    - 若实现需要读取密钥等配置，请从 app.config.settings 读取，并在 .env.example 补充说明
"""


def understand_image(image_path: str) -> str:
    raise NotImplementedError(
        "图片语义理解模块尚未接入：请用真实实现替换 app/clients/image_understanding.py，"
        "或在 .env 中设置 USE_MOCK=true 使用模拟数据"
    )
