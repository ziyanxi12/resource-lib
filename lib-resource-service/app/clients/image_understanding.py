"""
图片语义理解模块（占位）
======================================================
此文件由图片理解模块的提供方用真实实现整体替换。

约定接口：
    understand_image(image: str, prompt: Optional[str] = None, image_is_base64: bool = False) -> str
    - image: 当 image_is_base64=True 时为前端构造的图片 base64 字符串（不含 data: 前缀）；
             当 image_is_base64=False 时为图片文件的绝对路径。
    - prompt: 用户提示词（可选），用于引导生成方向
    - 返回: 图片的中文语义描述文本
    - 失败时抛出异常，由上层统一捕获处理
    - 若实现需要读取密钥等配置，请从 app.config.settings 读取，并在 .env.example 补充说明

说明：
    优先使用前端传入的 base64（image_is_base64=True），后端不再从磁盘读文件；
    为兼容旧调用方式，仍保留 image_is_base64=False 的路径读取分支作为兜底。
"""


def understand_image(image: str, prompt: str = None, image_is_base64: bool = False) -> str:
    raise NotImplementedError(
        "图片语义理解模块尚未接入：请用真实实现替换 app/clients/image_understanding.py，"
        "或在 .env 中设置 USE_MOCK=true 使用模拟数据"
    )
