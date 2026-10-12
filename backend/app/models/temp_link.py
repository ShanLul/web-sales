"""临时链接：子系统访问凭证，携带有效期与可用次数约束。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LinkStatus
from app.models.permission import PermissionTemplate


class TempLink(Base):
    __tablename__ = "temp_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("permission_template.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # NULL 表示永久有效
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # NULL 表示不限次数
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 下单成功即失效
    is_single_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=LinkStatus.ACTIVE.value, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    template: Mapped["PermissionTemplate"] = relationship(PermissionTemplate)
