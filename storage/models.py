"""
数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawNewsItem:
    """采集到的原始新闻条目"""
    title: str
    url: str
    source_name: str           # 数据源显示名
    source_type: str           # rss / google_news / web / linkedin
    language: str              # zh / en
    authority_score: int       # 信源权威度得分 (4-10)
    summary: str = ""
    published_at: Optional[datetime] = None
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScoredNewsItem:
    """经过评分处理的新闻条目"""
    # 基础信息（从 RawNewsItem 继承）
    title: str
    url: str
    source_name: str
    source_type: str
    language: str
    summary: str
    published_at: Optional[datetime]
    collected_at: datetime

    # 评分明细
    authority_score: int       # 信源权威度 (因子1)
    company_score: int         # 公司重要性 (因子2)
    company_name: str          # 识别到的公司名（最相关的一个）
    innovation_score: int      # 创新相关性 (因子3)
    innovation_label: str      # 创新类型标签
    recency_score: int         # 时效性 (因子4)
    buzz_score: int            # 热度信号 (因子5, 默认5)

    # 加权总分
    total_score: float = 0.0

    def to_dict(self) -> dict:
        """转为字典，方便数据库存储"""
        return {
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "language": self.language,
            "summary": self.summary,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "collected_at": self.collected_at.isoformat(),
            "authority_score": self.authority_score,
            "company_score": self.company_score,
            "company_name": self.company_name,
            "innovation_score": self.innovation_score,
            "innovation_label": self.innovation_label,
            "recency_score": self.recency_score,
            "buzz_score": self.buzz_score,
            "total_score": self.total_score,
        }
