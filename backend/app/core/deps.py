"""FastAPI 依赖注入：数据库会话、当前管理员。"""

from typing import Annotated, Optional

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.admin import Admin
from app.utils.exceptions import AuthError

DbSession = Annotated[Session, Depends(get_db)]


def get_current_admin(
    db: DbSession,
    authorization: Annotated[Optional[str], Header()] = None,
) -> Admin:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError()
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise AuthError() from exc

    admin_id = payload.get("sub")
    if not admin_id:
        raise AuthError()

    admin = db.get(Admin, int(admin_id))
    if admin is None or not admin.is_active:
        raise AuthError("账号不存在或已停用")
    return admin


CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]
