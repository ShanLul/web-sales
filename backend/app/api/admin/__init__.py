"""主系统（管理后台）路由汇聚。"""

from fastapi import APIRouter

from app.api.admin import auth, exports, links, orders, permissions, products

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(auth.router)
admin_router.include_router(products.router)
admin_router.include_router(products.category_router)
admin_router.include_router(permissions.router)
admin_router.include_router(links.router)
admin_router.include_router(orders.router)
admin_router.include_router(exports.router)

__all__ = ["admin_router"]
