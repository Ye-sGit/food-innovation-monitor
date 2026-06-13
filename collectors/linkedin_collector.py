"""
LinkedIn 采集器 — 公司动态 + KOL/创始人帖子

使用 linkedin-api 非官方库，抓取:
1. 食品巨头/创业公司官方动态
2. 行业 KOL / 创始人个人帖子

⚠️ 风险: 非官方 API，建议用非主力 LinkedIn 账号。
   如被封可改用第三方合规 API（Apify, Proxycurl）。

启用方法: 在 .env 中填写 LINKEDIN_EMAIL 和 LINKEDIN_PASSWORD
"""

from typing import List
from datetime import datetime, timezone

from collectors.base import BaseCollector
from storage.models import RawNewsItem
from config.settings import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from utils.logger import get_logger

logger = get_logger(__name__)

# ═══════════════════════════════════════════════
# 监控目标
# ═══════════════════════════════════════════════

# 食品饮料公司（LinkedIn public_id）
TARGET_COMPANIES = [
    # 全球巨头
    "nestle", "pepsico", "coca-cola", "unilever", "danone",
    "mondelez", "kraft-heinz", "generalmills", "mars", "tyson-foods",
    # 创新食品
    "beyond-meat", "oatly", "impossible-foods", "kellogg", "hershey",
    "eat-just", "perfect-day-foods", "notco", "nature's-fynd",
    # 饮料
    "suntory", "red-bull", "monster-energy",
    # 中国食品出海
    "yihai-kerry", "want-want-china", "china-mengniu-dairy",
]

# 行业 KOL / 创始人 / 投资人（LinkedIn username）
TARGET_KOLS = [
    # 替代蛋白/食品科技投资人
    "brucefriedrich",          # GFI 创始人
    "patbrown",                # Impossible Foods 创始人
    "ethanbrown11",            # Beyond Meat CEO
    "joshtetrick",             # Eat Just CEO
    # 食品创新 KOL
    "michael-wolf-5802",       # The Spoon 创始人（食品科技媒体）
    "brittanysaun",            # FoodTech Weekly
    # 可根据兴趣自行添加更多
]


class LinkedInCollector(BaseCollector):
    """LinkedIn 公司+KOL 动态采集器"""

    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.enabled = bool(LINKEDIN_EMAIL and LINKEDIN_PASSWORD)
        self.api = None

    def _init_api(self):
        """延迟初始化 LinkedIn API"""
        if self.api is not None:
            return True
        if not self.enabled:
            return False

        try:
            from linkedin_api import Linkedin
            self.api = Linkedin(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
            logger.info("LinkedIn API 初始化成功")
            return True
        except ImportError:
            logger.warning(
                "linkedin-api 未安装，跳过 LinkedIn 采集。"
                "安装: pip install linkedin-api"
            )
            self.enabled = False
            return False
        except Exception as e:
            logger.error(f"LinkedIn 登录失败: {e}")
            self.enabled = False
            return False

    def _fetch_company_posts(self, company_id: str) -> List[RawNewsItem]:
        """采集单个公司的最新动态"""
        items = []
        try:
            updates = self.api.get_company_updates(
                public_id=company_id,
                max_results=5,
            )
        except Exception as e:
            logger.debug(f"LinkedIn 公司 [{company_id}] 异常: {e}")
            return items

        for update in updates:
            try:
                content = (
                    update.get("commentary", {})
                    .get("text", {})
                    .get("text", "")
                )
                if not content:
                    continue

                title = content[:120].replace("\n", " ")
                link = f"https://www.linkedin.com/company/{company_id}/"

                # 尝试获取发布时间
                published_at = None
                raw_time = update.get("createdAt") or update.get("timestamp")
                if raw_time:
                    try:
                        published_at = datetime.fromtimestamp(
                            raw_time / 1000, tz=timezone.utc
                        )
                    except Exception:
                        pass

                items.append(self._make_item(
                    title=title,
                    url=link,
                    summary=content[:300],
                    language="en",
                    published_at=published_at,
                ))
            except Exception:
                continue
        return items

    def _fetch_profile_posts(self, username: str) -> List[RawNewsItem]:
        """采集单个 KOL/个人的最新帖子"""
        items = []
        try:
            # linkedin-api 获取个人帖子
            posts = self.api.get_profile_posts(
                public_id=username,
                post_count=5,
            )
        except Exception as e:
            logger.debug(f"LinkedIn 个人 [{username}] 异常: {e}")
            return items

        for post in posts:
            try:
                content = (
                    post.get("commentary", {})
                    .get("text", {})
                    .get("text", "")
                )
                if not content:
                    continue

                author = (
                    post.get("author", {})
                    .get("name", username)
                )
                title = f"[{author}] {content[:100].replace(chr(10), ' ')}"
                link = f"https://www.linkedin.com/in/{username}/"

                published_at = None
                raw_time = post.get("createdAt") or post.get("timestamp")
                if raw_time:
                    try:
                        published_at = datetime.fromtimestamp(
                            raw_time / 1000, tz=timezone.utc
                        )
                    except Exception:
                        pass

                items.append(self._make_item(
                    title=title,
                    url=link,
                    summary=content[:300],
                    language="en",
                    published_at=published_at,
                ))
            except Exception:
                continue
        return items

    def fetch(self) -> List[RawNewsItem]:
        """采集所有目标"""
        if not self._init_api():
            logger.info("LinkedIn 采集已禁用（未配置账号）")
            return []

        all_items = []

        # 公司动态
        logger.info(f"采集 LinkedIn: {len(TARGET_COMPANIES)} 家公司 + {len(TARGET_KOLS)} 位 KOL")
        for company_id in TARGET_COMPANIES:
            items = self._fetch_company_posts(company_id)
            all_items.extend(items)

        # KOL / 创始人帖子
        for username in TARGET_KOLS:
            items = self._fetch_profile_posts(username)
            all_items.extend(items)

        logger.info(f"  └─ LinkedIn: 采集 {len(all_items)} 条")
        return all_items
