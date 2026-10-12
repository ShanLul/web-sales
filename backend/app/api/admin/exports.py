"""Excel 报表导出：订单数据与商品数据。

导出内容先写入临时文件，再以 FileResponse 流式回传，最后由后台任务删除临时文件，
避免 2C2G 机器上大表导出时内存被打满。
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.admin.orders import OrderFilterDep, build_stmt
from app.core.deps import CurrentAdmin, DbSession
from app.models.enums import ProductStatus
from app.models.product import Product
from app.services import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["主系统-导出"])


def _build_product_stmt(
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Select:
    stmt = select(Product).options(joinedload(Product.category), selectinload(Product.variants))
    if keyword and keyword.strip():
        stmt = stmt.where(Product.name.like(f"%{keyword.strip()}%"))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if status in (ProductStatus.ON_SALE.value, ProductStatus.OFF_SHELF.value):
        stmt = stmt.where(Product.status == status)
    return stmt


def _file_response(path: str, filename: str, background: BackgroundTasks) -> FileResponse:
    background.add_task(export_service.remove_file, path)
    return FileResponse(path, filename=filename, media_type=export_service.XLSX_MEDIA_TYPE)


@router.get("/orders")
def export_orders(
    db: DbSession,
    _admin: CurrentAdmin,
    filters: OrderFilterDep,
    background: BackgroundTasks,
):
    path = export_service.export_orders(db, build_stmt(filters))
    logger.info("导出订单数据 file=%s", path)
    return _file_response(path, export_service.build_filename("订单数据"), background)


@router.get("/products")
def export_products(
    db: DbSession,
    _admin: CurrentAdmin,
    background: BackgroundTasks,
    keyword: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    stmt = _build_product_stmt(keyword=keyword, category_id=category_id, status=status)
    products = db.execute(stmt.order_by(Product.id.desc())).scalars().unique().all()
    path = export_service.export_products(db, products)
    logger.info("导出商品数据 file=%s count=%s", path, len(products))
    return _file_response(path, export_service.build_filename("商品数据"), background)
