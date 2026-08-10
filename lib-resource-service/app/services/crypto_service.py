import base64
import json
import logging

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from app.config import settings

logger = logging.getLogger(__name__)

_KEY_BYTES = base64.b64decode(settings.AUTH_AES_KEY)


def decrypt_user_data(encrypted_b64: str) -> dict:
    """解密前端传来的 X-User-Data header。

    前端格式：Base64( IV(16) + AES-256-CBC ciphertext )
    返回：用户信息 dict（account, dept, deptcode, nickName, roleId, roles, uid, uuid）
    """
    raw = base64.b64decode(encrypted_b64)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = AES.new(_KEY_BYTES, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return json.loads(plaintext.decode("utf-8"))
