"""
多因子重要性评分算法（时效优先版）

评分公式:
  总分 = 信源权威度 × 0.20 + 公司重要性 × 0.15 + 创新相关性 × 0.25
        + 时效性 × 0.25 + 热度信号 × 0.15

评分前硬过滤: 超过 48 小时的新闻直接丢弃
时效性分档更细: 越靠近现在分越高
"""

from datetime import datetime, timezone, timedelta
from typing import List, Tuple

from storage.models import RawNewsItem, ScoredNewsItem
from processor.nlp_utils import classify_innovation, get_top_company
from config.settings import MAX_ARTICLE_AGE_HOURS
from utils.logger import get_logger

logger = get_logger(__name__)

# ── 权重配置（时效权重提升至 25%）─────────────────
WEIGHTS = {
    "authority": 0.20,    # 信源权威度
    "company": 0.15,      # 公司重要性
    "innovation": 0.25,   # 创新相关性
    "recency": 0.25,      # 时效性 ⬆（追热点核心）
    "buzz": 0.15,         # 热度信号 ⬆
}


def _calc_recency_score(published_at: datetime | None) -> int:
    """
    计算时效性得分（更细的分档）

    | 发布时长     | 得分 | 说明           |
    |------------|------|----------------|
    | < 2 小时    | 10   | 突发/实时热点   |
    | 2-6 小时    | 9    | 今天内         |
    | 6-12 小时   | 8    | 半天内         |
    | 12-24 小时  | 6    | 昨天           |
    | 24-36 小时  | 4    | 前天偏旧       |
    | 36-48 小时  | 2    | 快过期         |
    | > 48 小时   | 0    | 会被硬过滤     |
    """
    if published_at is None:
        return 4  # 未知时间保守给低分，不鼓励无时间戳的旧闻

    now = datetime.now(timezone.utc)

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    delta = now - published_at
    hours = delta.total_seconds() / 3600

    if hours < 2:
        return 10
    elif hours < 6:
        return 9
    elif hours < 12:
        return 8
    elif hours < 24:
        return 6
    elif hours < 36:
        return 4
    elif hours < 48:
        return 2
    else:
        return 0  # 超过 48 小时


def filter_old_articles(items: List[RawNewsItem]) -> List[RawNewsItem]:
    """
    硬过滤：丢弃发布时间超过 MAX_ARTICLE_AGE_HOURS 的新闻

    Args:
        items: 原始新闻列表

    Returns:
        只保留 48 小时内的新闻
    """
    if not items:
        return items

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=MAX_ARTICLE_AGE_HOURS)

    fresh = []
    old_count = 0
    no_date_count = 0

    for item in items:
        if item.published_at is None:
            # 没有发布时间的条目：保留但标记（在采集阶段已尽量解析）
            fresh.append(item)
            no_date_count += 1
            continue

        pub = item.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)

        if pub >= cutoff:
            fresh.append(item)
        else:
            old_count += 1

    if old_count > 0:
        logger.info(
            f"时效过滤: 丢弃 {old_count} 条超过 {MAX_ARTICLE_AGE_HOURS} 小时的旧闻, "
            f"保留 {len(fresh)} 条 (其中 {no_date_count} 条无时间戳)"
        )

    return fresh


def score_item(item: RawNewsItem) -> ScoredNewsItem:
    """
    对单条新闻进行多因子评分

    Args:
        item: 原始新闻条目

    Returns:
        已评分的 ScoredNewsItem
    """
    text = item.title + " " + item.summary

    # 因子 1: 信源权威度
    authority = item.authority_score

    # 因子 2: 公司重要性
    company_name, company_score = get_top_company(text)

    # 因子 3: 创新相关性
    innovation_score, innovation_label = classify_innovation(
        text, item.language
    )

    # 因子 4: 时效性（新分档）
    recency_score = _calc_recency_score(item.published_at)

    # 因子 5: 热度信号
    buzz_score = 5

    # 加权总分
    total = (
        authority * WEIGHTS["authority"]
        + company_score * WEIGHTS["company"]
        + innovation_score * WEIGHTS["innovation"]
        + recency_score * WEIGHTS["recency"]
        + buzz_score * WEIGHTS["buzz"]
    )

    return ScoredNewsItem(
        title=item.title,
        url=item.url,
        source_name=item.source_name,
        source_type=item.source_type,
        language=item.language,
        summary=item.summary,
        published_at=item.published_at,
        collected_at=item.collected_at,
        authority_score=authority,
        company_score=company_score,
        company_name=company_name,
        innovation_score=innovation_score,
        innovation_label=innovation_label,
        recency_score=recency_score,
        buzz_score=buzz_score,
        total_score=round(total, 1),
    )


def rank_items(items: List[RawNewsItem]) -> List[ScoredNewsItem]:
    """
    对一批新闻: 硬过滤 → 评分 → 排序

    Args:
        items: 原始新闻列表

    Returns:
        按 total_score 降序排列的 ScoredNewsItem 列表
    """
    # Step 0: 硬过滤旧闻
    items = filter_old_articles(items)
    logger.info(f"时效过滤后剩余: {len(items)} 条")

    # Step 1: 评分
    scored = [score_item(item) for item in items]

    # Step 2: 按总分降序
    scored.sort(key=lambda x: x.total_score, reverse=True)

    # 打印 Top 5 评分明细
    if scored:
        logger.info("── Top 5 评分明细 ──")
        for i, s in enumerate(scored[:5]):
            logger.info(
                f"  {i+1}. [{s.total_score:.1f}] {s.title[:60]}...\n"
                f"      信源={s.authority_score} 公司={s.company_name}({s.company_score}) "
                f"创新={s.innovation_label}({s.innovation_score}) "
                f"时效={s.recency_score} 热度={s.buzz_score}"
            )

    return scored


def split_top_items(
    scored_items: List[ScoredNewsItem],
    top_n: int = 10,
    secondary_n: int = 10,
) -> Tuple[List[ScoredNewsItem], List[ScoredNewsItem]]:
    """
    将已评分的新闻拆分为「最重要」和「次重要」两组
    """
    top_items = scored_items[:top_n]
    secondary_items = scored_items[top_n:top_n + secondary_n]
    return top_items, secondary_items
