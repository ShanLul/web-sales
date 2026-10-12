"""密码哈希、JWT 签发/解析、临时链接 token 生成。"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from app.core.config import settings

# bcrypt 仅使用前 72 字节，显式截断避免不同实现行为差异
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    raw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    raw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, extra: Optional[dict[str, Any]] = None) -> tuple[str, int]:
    """返回 (token, 有效期秒数)。"""
    now = datetime.now(timezone.utc)
    expires_in = settings.JWT_EXPIRE_MINUTES * 60
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def generate_link_token() -> str:
    """使用密码学安全随机数生成链接 token，防止被遍历猜测。"""
    return secrets.token_urlsafe(32)
