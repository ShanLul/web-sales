"""日志配置：控制台 + 文件双输出，按级别过滤。"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        # 避免 uvicorn reload 场景下重复添加 handler
        root.setLevel(level)
        return

    root.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(settings.LOG_DIR, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # 只读文件系统或权限不足时降级为仅控制台输出，不影响服务启动
        root.warning("日志目录不可写，已降级为仅控制台输出：%s", settings.LOG_DIR)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
