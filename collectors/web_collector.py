"""
中文媒体网页采集器
对无 RSS 的中文行业媒体网站进行标题列表抓取

使用 requests + BeautifulSoup 提取文章标题和链接
由于只抓取列表页的标题和链接（不进行全文爬取），
属于礼貌采集，不会对目标网站造成负担。
"""

from typing import List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from storage.models import RawNewsItem
from config.settings import REQUEST_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_SOURCE
from utils.logger import get_logger

logger = get_logger(__name__)


class WebCollector(BaseCollector):
    """网页列表采集器（针对中文媒体等无 RSS 的网站）"""

    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.url = source_config["url"]
        self.language = source_config.get("language", "zh")
        self.article_selector = source_config.get("article_selector", "article")
        self.title_selector = source_config.get("title_selector", "a")
        self.link_selector = source_config.get("link_selector", "a")
        self.base_url = source_config.get(
            "base_url",
            self._extract_base_url(self.url),
        )

    @staticmethod
    def _extract_base_url(url: str) -> str:
        """从完整 URL 提取 base URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _parse_url(self, href: str) -> str:
        """补全相对 URL 为绝对 URL"""
        if not href:
            return ""
        href = href.strip()
        if href.startswith("http"):
            return href
        if href.startswith("//"):
            return f"https:{href}"
        if href.startswith("/"):
            return f"{self.base_url}{href}"
        return f"{self.base_url}/{href}"

    def fetch(self) -> List[RawNewsItem]:
        """抓取标题列表"""
        items = []
        logger.info(f"采集网页: {self.name} ({self.url})")

        try:
            response = requests.get(
                self.url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            # 尝试检测编码
            response.encoding = response.apparent_encoding or "utf-8"
        except requests.RequestException as e:
            logger.error(f"网页请求失败 [{self.name}]: {e}")
            return items

        soup = BeautifulSoup(response.text, "lxml")

        # 尝试多种选择器策略
        articles = soup.select(self.article_selector)

        # 如果指定选择器没找到文章，尝试通用降级策略
        if not articles:
            logger.debug(f"  └─ 选择器 '{self.article_selector}' 无结果，尝试通用策略")
            articles = soup.select(
                "article a, div.news-item a, ul.newslist li a, "
                "div.article-list a, div.post a.title, div.content a[href]"
            )

        count = 0
        for article in articles[:MAX_ARTICLES_PER_SOURCE * 2]:
            # 提取标题和链接
            title_elem = article.select_one(
                self.title_selector
            ) or article
            link_elem = article.select_one(
                self.link_selector
            ) or article

            title = title_elem.get_text(strip=True)
            href = link_elem.get("href", "")

            # 过滤明显不是文章标题的文本
            if not title or not href:
                continue
            if len(title) < 6:  # 太短，可能是导航/分类名
                continue
            # 过滤页面公共元素
            skip_patterns = [
                "首页", "关于我们", "联系我们", "登录", "注册",
                "上一页", "下一页", "更多", "Home", "About",
                "Login", "Sign Up", "上一篇", "下一篇",
            ]
            if any(p in title for p in skip_patterns):
                continue

            count += 1
            items.append(
                self._make_item(
                    title=title,
                    url=self._parse_url(href),
                    language=self.language,
                )
            )

        # 去重（同一页面可能重复出现同篇文章）
        seen_urls = set()
        deduped = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                deduped.append(item)

        logger.info(f"  └─ {self.name}: 采集 {len(deduped)} 条")

        return deduped
