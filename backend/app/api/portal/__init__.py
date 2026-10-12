"""子系统路由汇聚（凭链接 token 访问，无需登录）。"""

from fastapi import APIRouter

from app.api.portal import catalog, checkout

portal_router = APIRouter(prefix="/portal")
portal_router.include_router(catalog.router)
portal_router.include_router(checkout.router)

__all__ = ["portal_router"]
