"""
Google News RSS 采集器

利用 Google News 的未公开 RSS 接口按关键词搜索新闻
URL 格式: https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en

注意：2024年中起 Google News RSS 返回的链接是 Base64 编码的重定向链接，
需要解码才能拿到原文 URL。本采集器只保留 RSS 标题+链接+发布时间，
不解码原文 URL（编码链接在飞书卡片中仍可点击跳转 Google News）。
"""

from typing import List
from datetime import datetime
from time import mktime
from urllib.parse import quote, urlencode

import feedparser

from collectors.base import BaseCollector
from storage.models import RawNewsItem
from config.settings import REQUEST_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_SOURCE
from config.sources import GOOGLE_NEWS_PARAMS, GOOGLE_NEWS_PARAMS_CN
from utils.logger import get_logger

logger = get_logger(__name__)


class GoogleNewsCollector(BaseCollector):
    """Google News RSS 搜索采集器"""

    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.searches = source_config.get("searches", [])
        self.language = source_config.get("language", "en")

        # 选择对应的默认参数
        if self.language == "zh-CN":
            self.default_params = GOOGLE_NEWS_PARAMS_CN.copy()
        else:
            self.default_params = GOOGLE_NEWS_PARAMS.copy()

    def _build_url(self, query: str) -> str:
        """构造 Google News RSS 搜索 URL"""
        params = self.default_params.copy()
        if self.language == "zh-CN":
            # 中文源 7 天窗口，兼顾数量和时效（评分器再做 48h 硬过滤）
            params["q"] = f"{query} when:7d"
        else:
            # 英文源限定最近 2 天
            params["q"] = f"{query} when:2d"
        return f"{self.BASE_URL}?{urlencode(params, quote_via=quote)}"

    def _fetch_one_query(self, query: str) -> List[RawNewsItem]:
        """对单个搜索词采集"""
        url = self._build_url(query)
        items = []

        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
        except Exception as e:
            logger.error(f"Google News 采集失败 [{query}]: {e}")
            return items

        if feed.bozo and not feed.entries:
            logger.warning(f"Google News Bozo [{query}]: {feed.bozo_exception}")
            return items

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            # 去掉 Google News 标题末尾的 " - SourceName"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()

            link = entry.get("link", "").strip()

            if not title or not link:
                continue

            # 发布时间
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime.fromtimestamp(
                        mktime(entry.published_parsed)
                    )
                except (OverflowError, ValueError):
                    pass

            # 摘要
            summary = entry.get("summary", "")[:300]
            import re
            from html import unescape
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = unescape(summary).strip()

            # 提取来源名称
            source_name = self.name
            if hasattr(entry, "source") and entry.source:
                source_name = f"Google News ({entry.source.get('title', '')})"

            items.append(
                self._make_item(
                    title=title,
                    url=link,
                    summary=summary,
                    language=self.language,
                    published_at=published_at,
                )
            )

        return items

    def fetch(self) -> List[RawNewsItem]:
        """对所有搜索词采集并合并"""
        all_items = []
        logger.info(
            f"采集 Google News ({self.language}): {len(self.searches)} 个搜索词"
        )

        for query in self.searches:
            items = self._fetch_one_query(query)
            # 限制每个搜索词的结果数
            all_items.extend(items[:MAX_ARTICLES_PER_SOURCE])
            logger.debug(f"  └─ 搜索词 [{query}]: {len(items)} 条")

        # 用标题去重（Google News 不同搜索词可能返回相同文章）
        seen_titles = set()
        deduped = []
        for item in all_items:
            key = item.title.lower()[:60]
            if key not in seen_titles:
                seen_titles.add(key)
                deduped.append(item)

        logger.info(
            f"  └─ Google News ({self.language}): "
            f"采集 {len(all_items)} 条, 去重后 {len(deduped)} 条"
        )
        return deduped
