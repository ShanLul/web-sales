"""订单相关的请求/响应模型。"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderItemIn(BaseModel):
    product_id: int = Field(..., ge=1)
    # 无规格商品不传；有规格商品必须传，服务端会校验归属与在售状态
    variant_id: Optional[int] = Field(None, ge=1)
    quantity: int = Field(..., ge=1, le=9999)


class PortalOrderCreate(BaseModel):
    """子系统匿名下单入参：只提交 token 与商品 id/规格/数量，授权范围由服务端推导。"""

    token: str = Field(..., min_length=8, max_length=128)
    customer_name: str = Field(..., min_length=1, max_length=50)
    customer_phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    customer_address: str = Field(..., min_length=5, max_length=200)
    remark: Optional[str] = Field(None, max_length=200)
    items: list[OrderItemIn] = Field(..., min_length=1)

    @field_validator("items")
    @classmethod
    def _merge_same_product(cls, value: list[OrderItemIn]) -> list[OrderItemIn]:
        """同一商品的不同规格是独立明细行，因此按「商品 + 规格」合并。"""
        merged: dict[tuple[int, Optional[int]], int] = {}
        for item in value:
            key = (item.product_id, item.variant_id)
            merged[key] = merged.get(key, 0) + item.quantity
            if merged[key] > 9999:
                raise ValueError("单个商品数量不能超过 9999")
        return [
            OrderItemIn(product_id=pid, variant_id=vid, quantity=qty)
            for (pid, vid), qty in merged.items()
        ]


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "shipped", "completed", "cancelled"]


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    product_name: str
    variant_name: Optional[str] = None
    price: float
    quantity: int
    subtotal: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    link_id: Optional[int] = None
    link_remark: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_address: str
    remark: Optional[str] = None
    total_amount: float
    status: str
    status_label: str = ""
    item_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[OrderItemOut] = Field(default_factory=list)


class OrderCreatedOut(BaseModel):
    order_no: str
    total_amount: float
    created_at: Optional[datetime] = None


class LinkInfoOut(BaseModel):
    """子系统进入时使用的链接信息。"""

    remark: Optional[str] = None
    expire_at: Optional[datetime] = None
    remaining_uses: Optional[int] = None
    is_single_use: bool = False
    template_name: Optional[str] = None


class PortalCatalogOut(BaseModel):
    link: LinkInfoOut
    categories: list[dict] = Field(default_factory=list)
    products: list[dict] = Field(default_factory=list)
