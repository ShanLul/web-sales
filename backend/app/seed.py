"""初始化脚本：创建默认管理员与可选演示数据。

用法：
    python -m app.seed                # 仅创建默认管理员
    python -m app.seed --with-demo    # 额外写入分类 / 商品 / 权限模板 / 演示链接
"""

import argparse
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.logging_config import setup_logging
from app.core.security import generate_link_token, hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin
from app.models.enums import LinkStatus
from app.models.permission import PermissionTemplate
from app.models.product import Category, Product, ProductVariant
from app.models.temp_link import TempLink

logger = logging.getLogger("app.seed")

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

DEMO_CATEGORIES = [
    ("办公耗材", 1),
    ("数码配件", 2),
    ("智能家居", 3),
]

DEMO_PRODUCTS = [
    ("A4 复印纸 500 张装", "OF-1001", "办公耗材", "42.00", "包", "80g 高白度双胶纸，适合激光打印与复印", "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=600&q=80"),
    ("中性签字笔 0.5mm 十支装", "OF-1002", "办公耗材", "19.90", "盒", "顺滑速干墨水，考试办公通用", "https://images.unsplash.com/photo-1585336261022-680e295ce3fe?w=600&q=80"),
    ("桌面收纳文件框", "OF-1003", "办公耗材", "35.00", "个", "三层可拆卸结构，承重稳定不塌陷", "https://images.unsplash.com/photo-1519974719765-e6559eac2575?w=600&q=80"),
    ("65W 氮化镓充电器", "DG-2001", "数码配件", "129.00", "个", "双 C 口输出，兼容笔记本与手机快充", "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&q=80"),
    ("编织数据线 1.5 米", "DG-2002", "数码配件", "29.00", "条", "支持 100W 快充，尼龙编织抗弯折", "https://images.unsplash.com/photo-1615526675159-e248c3021d3f?w=600&q=80"),
    ("无线双模鼠标", "DG-2003", "数码配件", "89.00", "个", "蓝牙 5.0 与 2.4G 双模切换，静音微动", "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&q=80"),
    ("智能温湿度计", "SH-3001", "智能家居", "79.00", "台", "电子墨水屏，支持米家 App 联动", "https://images.unsplash.com/photo-1545259741-2ea3ebf61fa3?w=600&q=80"),
    ("智能门磁传感器", "SH-3002", "智能家居", "59.00", "套", "开合状态实时推送，超长续航", "https://images.unsplash.com/photo-1558002038-1055907df827?w=600&q=80"),
]

# 规格按商品 SKU 挂载：(规格名, 规格 SKU, 价格)
# 未列出的商品保持单一价格，方便对照两种形态在客户端的展示差异。
DEMO_VARIANTS: dict[str, list[tuple[str, str, str]]] = {
    "OF-1001": [
        ("500 张装", "OF-1001-500", "42.00"),
        ("5 包装", "OF-1001-5P", "199.00"),
    ],
    "DG-2001": [
        ("单 C 口 45W", "DG-2001-45W", "99.00"),
        ("双 C 口 65W", "DG-2001-65W", "129.00"),
        ("双 C 口 100W", "DG-2001-100W", "189.00"),
    ],
    "DG-2002": [
        ("1 米", "DG-2002-1M", "25.00"),
        ("1.5 米", "DG-2002-15M", "29.00"),
        ("2 米", "DG-2002-2M", "35.00"),
    ],
    "SH-3001": [
        ("白色", "SH-3001-W", "79.00"),
        ("黑色", "SH-3001-B", "79.00"),
    ],
}


def ensure_admin(db) -> Admin:
    admin = db.scalar(select(Admin).where(Admin.username == DEFAULT_USERNAME))
    if admin is not None:
        logger.info("管理员 %s 已存在，跳过创建", DEFAULT_USERNAME)
        return admin

    admin = Admin(
        username=DEFAULT_USERNAME,
        password_hash=hash_password(DEFAULT_PASSWORD),
        name="系统管理员",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info("已创建默认管理员 %s / %s，请登录后立即修改密码", DEFAULT_USERNAME, DEFAULT_PASSWORD)
    return admin


def seed_demo(db) -> None:
    if db.scalar(select(Category.id).limit(1)) is not None:
        logger.info("已存在业务数据，跳过演示数据写入")
        return

    category_map: dict[str, Category] = {}
    for name, sort_order in DEMO_CATEGORIES:
        category = Category(name=name, sort_order=sort_order)
        db.add(category)
        category_map[name] = category
    db.flush()

    products: list[Product] = []
    for name, sku, category_name, price, unit, description, image_url in DEMO_PRODUCTS:
        product = Product(
            name=name,
            sku=sku,
            category_id=category_map[category_name].id,
            price=Decimal(price),
            unit=unit,
            description=description,
            image_url=image_url,
            status="on_sale",
        )
        db.add(product)
        products.append(product)
    db.flush()

    variant_total = 0
    for product in products:
        rows = DEMO_VARIANTS.get(product.sku or "")
        if not rows:
            continue
        for index, (name, sku, price) in enumerate(rows):
            product.variants.append(
                ProductVariant(
                    name=name,
                    sku=sku,
                    price=Decimal(price),
                    sort_order=index,
                    status="on_sale",
                )
            )
        # 与后台保存保持同一口径：商品单价取在售规格的最低价作为起价
        product.price = min(Decimal(price) for _, _, price in rows)
        variant_total += len(rows)
    db.flush()

    template = PermissionTemplate(
        name="标准客户可见范围",
        description="演示用模板：可见办公耗材与数码配件全部商品",
        is_active=True,
    )
    db.add(template)
    db.flush()
    template.products = [item for item in products if item.category_id != category_map["智能家居"].id]

    link = TempLink(
        token=generate_link_token(),
        template_id=template.id,
        remark="演示链接（7 天有效 / 不限次数）",
        expire_at=datetime.now() + timedelta(days=7),
        max_uses=None,
        used_count=0,
        is_single_use=False,
        status=LinkStatus.ACTIVE.value,
        created_at=datetime.now(),
    )
    db.add(link)
    db.commit()

    logger.info(
        "演示数据写入完成：分类 %s 个、商品 %s 个、规格 %s 个",
        len(DEMO_CATEGORIES),
        len(products),
        variant_total,
    )
    logger.info("演示链接 token=%s", link.token)


def main() -> None:
    parser = argparse.ArgumentParser(description="web-sales 初始化脚本")
    parser.add_argument("--with-demo", action="store_true", help="同时写入演示分类/商品/模板/链接")
    args = parser.parse_args()

    setup_logging()
    db = SessionLocal()
    try:
        ensure_admin(db)
        if args.with_demo:
            seed_demo(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
