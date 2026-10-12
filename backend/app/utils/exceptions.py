"""业务异常与统一错误码。

约定：
- 业务失败返回 HTTP 200 + 非 0 的 code，前端统一提示；
- 鉴权失败返回 HTTP 401 + code 401；
- 子系统链接类错误额外携带 reason 字符串，供 H5 渲染不同失效文案。
"""

from typing import Optional


class ErrorCode:
    # 通用
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL = 500

    # 临时链接（子系统）
    LINK_NOT_FOUND = 1001
    LINK_EXPIRED = 1002
    LINK_EXHAUSTED = 1003
    LINK_DISABLED = 1004
    LINK_VOIDED = 1005

    # 子系统下单
    PRODUCT_NOT_AUTHORIZED = 1101
    PRODUCT_OFF_SHELF = 1102
    EMPTY_CART = 1103
    TOO_MANY_REQUESTS = 1104
    VARIANT_CHANGED = 1105


LINK_REASON_MAP = {
    ErrorCode.LINK_NOT_FOUND: "LINK_NOT_FOUND",
    ErrorCode.LINK_EXPIRED: "LINK_EXPIRED",
    ErrorCode.LINK_EXHAUSTED: "LINK_EXHAUSTED",
    ErrorCode.LINK_DISABLED: "LINK_DISABLED",
    ErrorCode.LINK_VOIDED: "LINK_VOIDED",
}


class BizError(Exception):
    """可预期的业务异常，由全局异常处理器转换为统一响应体。"""

    def __init__(
        self,
        message: str,
        code: int = ErrorCode.BAD_REQUEST,
        http_status: int = 200,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.reason = reason or LINK_REASON_MAP.get(code)


class AuthError(BizError):
    def __init__(self, message: str = "登录已失效，请重新登录") -> None:
        super().__init__(message, code=ErrorCode.UNAUTHORIZED, http_status=401)


class NotFoundError(BizError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code=ErrorCode.NOT_FOUND)


class ConflictError(BizError):
    def __init__(self, message: str = "数据冲突") -> None:
        super().__init__(message, code=ErrorCode.CONFLICT)
