"""
采集器基类
定义统一接口，所有采集器继承此类
"""

from abc import ABC, abstractmethod
from typing import List
from storage.models import RawNewsItem


class BaseCollector(ABC):
    """采集器抽象基类"""

    def __init__(self, source_config: dict):
        self.config = source_config
        self.name = source_config.get("name", self.__class__.__name__)
        self.authority_score = source_config.get("authority_score", 5)
        self.source_type = source_config.get("type", "unknown")

    @abstractmethod
    async def fetch(self) -> List[RawNewsItem]:
        """
        采集新闻条目
        返回 RawNewsItem 列表
        """
        ...

    def _make_item(
        self,
        title: str,
        url: str,
        summary: str = "",
        language: str = "en",
        **kwargs,
    ) -> RawNewsItem:
        """创建标准化的 RawNewsItem"""
        return RawNewsItem(
            title=title.strip(),
            url=url.strip(),
            source_name=self.name,
            source_type=self.source_type,
            language=language,
            authority_score=self.authority_score,
            summary=summary.strip(),
            **kwargs,
        )
