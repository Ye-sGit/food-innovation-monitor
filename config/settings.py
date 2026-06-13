"""
全局配置管理
从 .env 文件加载配置，提供默认值
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(PROJECT_ROOT / ".env")

# ── 飞书配置 ──────────────────────────────────
# 推送模式: "webhook" (群机器人) 或 "api" (个人推送)
FEISHU_MODE = os.getenv("FEISHU_MODE", "webhook")

# 模式 A: 群机器人 Webhook
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
FEISHU_WEBHOOK_SECRET = os.getenv("FEISHU_WEBHOOK_SECRET", "")

# 模式 B: 个人推送 API（App Bot）
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_USER_OPEN_ID = os.getenv("FEISHU_USER_OPEN_ID", "")

# ── LinkedIn 配置（可选）──────────────────────
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# ── 数据库配置 ────────────────────────────────
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(PROJECT_ROOT / "data" / "food_news.db"),
)

# ── 日志配置 ──────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"

# ── 采集配置 ──────────────────────────────────
REQUEST_TIMEOUT = 15  # HTTP 请求超时(秒)
MAX_ARTICLES_PER_SOURCE = 30  # 每个数据源最多采集条数
MAX_ARTICLE_AGE_HOURS = 48  # 超过此时间的新闻直接丢弃
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ── 推送配置 ──────────────────────────────────
TOP_IMPORTANT_COUNT = 10   # 「最重要」热点数量
TOP_SECONDARY_COUNT = 10   # 「次重要」热点数量

# ── 确保必要的目录存在 ────────────────────────
(Path(DATABASE_PATH).parent).mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
