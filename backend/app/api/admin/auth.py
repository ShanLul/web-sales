"""管理员登录与登录态查询。"""

import logging

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentAdmin, DbSession
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.schemas.admin import AdminOut, LoginIn
from app.schemas.common import ok
from app.utils.exceptions import BizError, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["主系统-登录"])


@router.post("/login")
def login(payload: LoginIn, db: DbSession):
    admin = db.scalar(select(Admin).where(Admin.username == payload.username))
    if admin is None or not verify_password(payload.password, admin.password_hash):
        logger.warning("登录失败：账号或密码错误 username=%s", payload.username)
        raise BizError("账号或密码错误", ErrorCode.BAD_REQUEST)
    if not admin.is_active:
        raise BizError("账号已停用，请联系系统管理员", ErrorCode.FORBIDDEN)

    token, expires_in = create_access_token(str(admin.id), {"username": admin.username})
    logger.info("管理员登录成功 username=%s", admin.username)
    return ok(
        {
            "token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "admin": AdminOut(id=admin.id, username=admin.username, name=admin.name or admin.username),
        }
    )


@router.get("/profile")
def profile(admin: CurrentAdmin):
    return ok(AdminOut(id=admin.id, username=admin.username, name=admin.name or admin.username))
