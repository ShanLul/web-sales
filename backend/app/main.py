"""FastAPI 应用入口：注册路由、CORS、统一异常处理与统一响应体。"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.admin import admin_router
from app.api.portal import portal_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.schemas.common import fail, ok
from app.utils.exceptions import LINK_REASON_MAP, BizError, ErrorCode

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="web-sales 主系统接口",
    description="主系统管理后台 + 临时链接下单子系统统一后端",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix=settings.API_PREFIX)
app.include_router(portal_router, prefix=settings.API_PREFIX)

_FIELD_LABELS = {
    "username": "账号",
    "password": "密码",
    "name": "名称",
    "token": "链接凭证",
    "t": "链接凭证",
    "price": "价格",
    "quantity": "数量",
    "items": "商品明细",
    "product_ids": "可见商品",
    "template_id": "权限模板",
    "expire_at": "到期时间",
    "max_uses": "可用次数",
    "customer_name": "收货人姓名",
    "customer_phone": "手机号",
    "customer_address": "收货地址",
    "remark": "备注",
    "status": "状态",
    "page": "页码",
    "page_size": "每页条数",
}


def _field_label(loc: tuple) -> str:
    parts = [str(item) for item in loc if item not in ("body", "query", "path")]
    if not parts:
        return "请求参数"
    head = parts[0]
    return _FIELD_LABELS.get(head, head)


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "请求参数不合法"
    first = errors[0]
    label = _field_label(tuple(first.get("loc", ())))
    error_type = first.get("type", "")
    raw = str(first.get("msg", ""))
    if error_type == "missing":
        return f"{label}不能为空"
    if error_type in {"string_pattern_mismatch", "value_error"}:
        if error_type == "value_error" and raw.startswith("Value error, "):
            return raw.removeprefix("Value error, ")
        return f"{label}格式不正确"
    if error_type in {"string_too_short", "too_short"}:
        return f"{label}长度不足"
    if error_type in {"string_too_long", "too_long"}:
        return f"{label}长度超出限制"
    if error_type in {"greater_than_equal", "less_than_equal", "greater_than", "less_than"}:
        return f"{label}数值超出允许范围"
    return f"{label}参数不合法"


@app.exception_handler(BizError)
async def handle_biz_error(_request: Request, exc: BizError) -> JSONResponse:
    if exc.code in LINK_REASON_MAP:
        logger.warning("链接校验失败 reason=%s message=%s", exc.reason, exc.message)
    else:
        logger.info("业务异常 code=%s message=%s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.http_status,
        content=fail(exc.code, exc.message, exc.reason),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    message = _validation_message(exc)
    logger.info("参数校验失败：%s", message)
    return JSONResponse(status_code=200, content=fail(ErrorCode.BAD_REQUEST, message))


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(exc.status_code, str(exc.detail or "请求失败")),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # 错误日志不整体 dump 请求体，避免把客户收货信息写进日志
    logger.exception("未处理异常 path=%s method=%s", request.url.path, request.method)
    return JSONResponse(status_code=500, content=fail(ErrorCode.INTERNAL, "服务内部错误，请稍后重试"))


@app.get(f"{settings.API_PREFIX}/health", tags=["系统"])
def health():
    return ok({"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION})
