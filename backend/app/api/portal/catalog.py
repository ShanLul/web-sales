"""子系统：凭 token 换取链接信息与授权商品列表。

未授权商品在这里就不会出现在响应中；下单时服务端还会再校验一次，双重防护。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from app.core.deps import DbSession
from app.schemas.common import ok
from app.services import link_service, permission_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["子系统-商品"])


@router.get("")
def get_catalog(
    db: DbSession,
    t: str = Query(..., min_length=8, max_length=128, description="临时链接 token"),
    category_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None, max_length=50),
):
    link = link_service.get_valid_link(db, t)
    products = permission_service.visible_products(
        db, link.template_id, only_on_sale=True, keyword=keyword
    )
    if category_id:
        products = [item for item in products if item.category_id == category_id]

    link_service.mark_accessed(db, link)

    categories: dict[int, str] = {}
    payload = []
    for item in products:
        variants = item.on_sale_variants
        # 规格全部下架的商品，在该链接里没有任何可售内容，直接不下发
        if item.variants and not variants:
            continue
        if item.category_id is not None:
            categories.setdefault(item.category_id, item.category.name if item.category else "")
        payload.append(
            {
                "id": item.id,
                "name": item.name,
                # 多规格商品对外展示起价，具体价格在选定规格后再确定
                "price": min(float(variant.price) for variant in variants)
                if variants
                else float(item.price),
                "unit": item.unit,
                "image_url": item.image_url,
                "description": item.description,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "variants": [
                    {
                        "id": variant.id,
                        "name": variant.name,
                        "price": float(variant.price),
                        "image_url": variant.image_url,
                    }
                    for variant in variants
                ],
            }
        )

    return ok(
        {
            "link": {
                "remark": link.remark,
                "expire_at": link.expire_at,
                "remaining_uses": link_service.remaining_uses(link),
                "is_single_use": link.is_single_use,
                "template_name": link.template.name if link.template else None,
            },
            "categories": [{"id": key, "name": name} for key, name in sorted(categories.items())],
            "products": payload,
        }
    )
