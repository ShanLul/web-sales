"""统一响应体与分页结构。"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    """成功响应。"""
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, reason: str | None = None) -> dict[str, Any]:
    """失败响应。"""
    return {"code": code, "message": message, "data": {"reason": reason} if reason else None}


class PageQuery(BaseModel):
    page: int = 1
    page_size: int = 10

    @property
    def offset(self) -> int:
        return (max(self.page, 1) - 1) * self.page_size


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "PageResult[T]":
        return cls(items=items, total=total, page=page, page_size=page_size)
