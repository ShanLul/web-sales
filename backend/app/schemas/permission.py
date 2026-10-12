"""权限模板的请求/响应模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    product_ids: list[int] = Field(default_factory=list)

    @field_validator("product_ids")
    @classmethod
    def _dedup(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    product_ids: Optional[list[int]] = None

    @field_validator("product_ids")
    @classmethod
    def _dedup(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        return list(dict.fromkeys(value)) if value is not None else None


class TemplateDuplicate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    product_count: int = 0
    product_ids: list[int] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
