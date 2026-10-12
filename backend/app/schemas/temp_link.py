"""临时链接的请求/响应模型。

有效期与可用次数由生成时逐项选择：
- expire_mode = permanent（永久）| custom（指定到期时间）
- use_mode    = unlimited（不限次数）| limited（指定次数）
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class TempLinkCreate(BaseModel):
    template_id: int = Field(..., ge=1)
    remark: Optional[str] = Field(None, max_length=200)

    expire_mode: Literal["permanent", "custom"] = "permanent"
    expire_at: Optional[datetime] = None

    use_mode: Literal["unlimited", "limited"] = "unlimited"
    max_uses: Optional[int] = Field(None, ge=1, le=100000)

    is_single_use: bool = False

    @model_validator(mode="after")
    def _validate_options(self) -> "TempLinkCreate":
        if self.expire_mode == "custom":
            if self.expire_at is None:
                raise ValueError("选择自定义有效期时必须填写到期时间")
            if self.expire_at <= datetime.now():
                raise ValueError("到期时间必须晚于当前时间")
        else:
            self.expire_at = None

        if self.use_mode == "limited" and not self.max_uses:
            raise ValueError("选择限制次数时必须填写可用次数")
        if self.use_mode == "unlimited":
            self.max_uses = None

        return self


class TempLinkStatusUpdate(BaseModel):
    status: Literal["active", "disabled"]


class TempLinkOut(BaseModel):
    id: int
    token: str
    url: str
    template_id: int
    template_name: Optional[str] = None
    remark: Optional[str] = None
    expire_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    used_count: int = 0
    remaining_uses: Optional[int] = None
    is_single_use: bool = False
    status: str
    derived_status: str
    status_label: str
    created_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
