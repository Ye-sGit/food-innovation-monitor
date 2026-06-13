"""
日志配置
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime

from config.settings import LOG_LEVEL, LOG_DIR


# 修复 Windows GBK 控制台无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    # 设置 PYTHONIOENCODING 环境变量（子进程继承）
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


class _SafeStreamHandler(logging.StreamHandler):
    """安全的控制台处理器，遇到编码错误时替换而非崩溃"""

    def emit(self, record):
        try:
            super().emit(record)
        except Exception:
            # 编码错误时降级处理：移除 emoji 后重试
            try:
                record.msg = (
                    str(record.msg)
                    .encode("ascii", errors="replace")
                    .decode("ascii")
                )
                super().emit(record)
            except Exception:
                pass


def get_logger(name: str) -> logging.Logger:
    """获取命名日志记录器"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # 控制台处理器 — 安全处理 emoji 编码
    console_handler = _SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)

    # 文件处理器 — 按日期滚动的日志文件
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        LOG_DIR / f"monitor-{today}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
