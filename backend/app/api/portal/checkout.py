"""子系统：匿名下单提交。

防刷单：按 token 做进程内滑动窗口节流（单进程部署下足够），
链接可用性、授权范围、次数扣减全部在服务端完成。
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock

from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import DbSession
from app.schemas.common import ok
from app.schemas.order import PortalOrderCreate
from app.services import order_service
from app.utils.exceptions import BizError, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["子系统-下单"])

_rate_lock = Lock()
_rate_buckets: dict[str, deque] = defaultdict(deque)
_MAX_BUCKETS = 5000


def check_rate_limit(token: str) -> None:
    limit = settings.PORTAL_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    now = datetime.now()
    window_start = now - timedelta(minutes=1)
    with _rate_lock:
        bucket = _rate_buckets[token]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit:
            raise BizError("提交过于频繁，请稍后再试", ErrorCode.TOO_MANY_REQUESTS)
        bucket.append(now)

        if len(_rate_buckets) > _MAX_BUCKETS:
            for key in [key for key, value in _rate_buckets.items() if not value]:
                _rate_buckets.pop(key, None)


@router.post("")
def submit_order(payload: PortalOrderCreate, db: DbSession):
    check_rate_limit(payload.token)
    order = order_service.create_portal_order(db, payload)
    logger.info(
        "子系统下单成功 order_no=%s link_id=%s 商品数=%s 金额=%s",
        order.order_no,
        order.link_id,
        len(payload.items),
        order.total_amount,
    )
    return ok(
        {
            "order_no": order.order_no,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at,
        }
    )
