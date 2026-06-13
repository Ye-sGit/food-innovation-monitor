"""
RSS 采集器
使用 feedparser 解析标准 RSS/Atom 源
"""

from typing import List
from datetime import datetime
from time import mktime

import feedparser

from collectors.base import BaseCollector
from storage.models import RawNewsItem
from config.settings import REQUEST_TIMEOUT, USER_AGENT
from utils.logger import get_logger

logger = get_logger(__name__)


class RssCollector(BaseCollector):
    """标准 RSS/Atom 采集器"""

    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.url = source_config["url"]
        self.language = source_config.get("language", "en")

    def fetch(self) -> List[RawNewsItem]:
        """解析 RSS 并返回条目列表"""
        items = []
        logger.info(f"采集 RSS: {self.name} ({self.url})")

        try:
            # feedparser 自带 User-Agent 可能被拒，尝试传递
            feed = feedparser.parse(
                self.url,
                agent=USER_AGENT,
            )
        except Exception as e:
            logger.error(f"RSS 解析失败 [{self.name}]: {e}")
            return items

        # 检查是否有解析错误
        if feed.bozo and not feed.entries:
            logger.warning(f"RSS Bozo 错误 [{self.name}]: {feed.bozo_exception}")
            return items

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                continue

            # 提取发布时间
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime.fromtimestamp(
                        mktime(entry.published_parsed)
                    )
                except (OverflowError, ValueError):
                    pass

            # 提取摘要
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:300]
            elif hasattr(entry, "description"):
                summary = entry.description[:300]

            # 去掉 HTML 标签
            from html import unescape
            import re
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = unescape(summary).strip()

            items.append(
                self._make_item(
                    title=title,
                    url=link,
                    summary=summary,
                    language=self.language,
                    published_at=published_at,
                )
            )

        logger.info(f"  └─ {self.name}: 采集 {len(items)} 条")
        return items
