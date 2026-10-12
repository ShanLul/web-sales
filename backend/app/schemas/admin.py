"""管理员相关请求模型。"""

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class AdminOut(BaseModel):
    id: int
    username: str
    name: str
