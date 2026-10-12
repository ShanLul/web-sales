"""商品与分类的请求/响应模型。金额在响应中统一输出为 float，内部计算仍用 Decimal。"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProductStatus

_PRODUCT_STATUS_VALUES = {item.value for item in ProductStatus}


def _normalize_price(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = Field(0, ge=0, le=9999)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0, le=9999)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    product_count: int = 0
    created_at: Optional[datetime] = None


class VariantIn(BaseModel):
    """商品规格入参。单维度互斥列表，整体替换式保存。"""

    name: str = Field(..., min_length=1, max_length=50)
    sku: Optional[str] = Field(None, max_length=50)
    price: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("9999999.99"))
    image_url: Optional[str] = Field(None, max_length=500)
    status: str = ProductStatus.ON_SALE.value

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("规格名称不能为空")
        return text

    @field_validator("sku")
    @classmethod
    def _blank_sku_to_none(cls, value: Optional[str]) -> Optional[str]:
        text = (value or "").strip()
        return text or None

    @field_validator("price")
    @classmethod
    def _quantize(cls, value: Decimal) -> Decimal:
        return _normalize_price(value)

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        if value not in _PRODUCT_STATUS_VALUES:
            raise ValueError("规格状态只能是 on_sale 或 off_shelf")
        return value


def _check_variant_list(value: Optional[list[VariantIn]]) -> Optional[list[VariantIn]]:
    """列表内部自检：重名与重复 SKU 在入库前就拦掉，避免落到数据库唯一约束报错。"""
    if value is None:
        return None
    if len(value) > 50:
        raise ValueError("单个商品最多支持 50 个规格")
    names = [item.name for item in value]
    if len(names) != len(set(names)):
        raise ValueError("规格名称不能重复")
    skus = [item.sku for item in value if item.sku]
    if len(skus) != len(set(skus)):
        raise ValueError("规格 SKU 不能重复")
    return value


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = None
    price: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("9999999.99"))
    unit: str = Field("件", min_length=1, max_length=20)
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = ProductStatus.ON_SALE.value
    variants: Optional[list[VariantIn]] = None

    @field_validator("price")
    @classmethod
    def _quantize(cls, value: Decimal) -> Decimal:
        return _normalize_price(value)

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        if value not in _PRODUCT_STATUS_VALUES:
            raise ValueError("商品状态只能是 on_sale 或 off_shelf")
        return value

    @field_validator("variants")
    @classmethod
    def _check_variants(cls, value: Optional[list[VariantIn]]) -> Optional[list[VariantIn]]:
        return _check_variant_list(value)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, ge=0, le=Decimal("9999999.99"))
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None
    # 传 null 表示不改动规格，传 [] 表示清空规格
    variants: Optional[list[VariantIn]] = None

    @field_validator("price")
    @classmethod
    def _quantize(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        return _normalize_price(value) if value is not None else None

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in _PRODUCT_STATUS_VALUES:
            raise ValueError("商品状态只能是 on_sale 或 off_shelf")
        return value

    @field_validator("variants")
    @classmethod
    def _check_variants(cls, value: Optional[list[VariantIn]]) -> Optional[list[VariantIn]]:
        return _check_variant_list(value)


class ProductStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        if value not in _PRODUCT_STATUS_VALUES:
            raise ValueError("商品状态只能是 on_sale 或 off_shelf")
        return value


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    status: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    price: float
    unit: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    status: str
    variants: list[VariantOut] = Field(default_factory=list)
    variant_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductBrief(BaseModel):
    """子系统商品卡片所需的最小字段集合。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    unit: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
