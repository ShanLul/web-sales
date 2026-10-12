"""应用配置：全部通过环境变量 / .env 注入。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "web-sales"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # ---- 数据库 ----
    DATABASE_URL: str = "sqlite:///./web_sales.db"
    DB_ECHO: bool = False
    # 2C2G 机器上连接池保持小规模，避免 MySQL 侧连接数被吃满
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE: int = 1800

    # ---- 鉴权 ----
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    # ---- 临时链接 ----
    PUBLIC_BASE_URL: str = "http://127.0.0.1:5174"
    PORTAL_RATE_LIMIT_PER_MINUTE: int = 10

    # ---- 跨域 ----
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://127.0.0.1:5174"

    # ---- 日志 ----
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    def build_portal_url(self, token: str) -> str:
        """拼接子系统完整访问链接（子系统使用 hash 路由，Nginx 无需额外 rewrite）。"""
        base = self.PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/#/order?t={token}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
