"""领域枚举。数据库中以字符串存储，便于跨 MySQL / SQLite 通用。"""

from enum import Enum


class ProductStatus(str, Enum):
    ON_SALE = "on_sale"      # 上架
    OFF_SHELF = "off_shelf"  # 下架


class TemplateStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LinkStatus(str, Enum):
    """持久化状态。"""

    ACTIVE = "active"      # 启用
    DISABLED = "disabled"  # 已禁用（可再次启用）
    VOIDED = "voided"      # 已作废（不可恢复）


class LinkDerivedStatus(str, Enum):
    """运行期派生状态，仅用于展示，不落库。"""

    UNUSED = "unused"        # 未使用
    IN_USE = "in_use"        # 使用中
    EXPIRED = "expired"      # 已过期
    EXHAUSTED = "exhausted"  # 次数耗尽
    DISABLED = "disabled"    # 已禁用
    VOIDED = "voided"        # 已作废


class OrderStatus(str, Enum):
    PENDING = "pending"      # 待发货
    SHIPPED = "shipped"      # 已发货
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


# 订单状态合法流转表：当前状态 -> 允许流转到的状态
ORDER_STATUS_FLOW = {
    OrderStatus.PENDING.value: [
        OrderStatus.SHIPPED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.SHIPPED.value: [
        OrderStatus.COMPLETED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.COMPLETED.value: [],
    OrderStatus.CANCELLED.value: [],
}

ORDER_STATUS_LABELS = {
    OrderStatus.PENDING.value: "待发货",
    OrderStatus.SHIPPED.value: "已发货",
    OrderStatus.COMPLETED.value: "已完成",
    OrderStatus.CANCELLED.value: "已取消",
}

LINK_STATUS_LABELS = {
    LinkDerivedStatus.UNUSED.value: "未使用",
    LinkDerivedStatus.IN_USE.value: "使用中",
    LinkDerivedStatus.EXPIRED.value: "已过期",
    LinkDerivedStatus.EXHAUSTED.value: "次数耗尽",
    LinkDerivedStatus.DISABLED.value: "已禁用",
    LinkDerivedStatus.VOIDED.value: "已作废",
}
