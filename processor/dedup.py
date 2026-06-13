"""
去重模块

两层去重策略:
1. URL 精确匹配 — 通过数据库查询已采集过的 URL
2. 标题相似度匹配 — 使用 difflib 检测相似标题（>0.8 阈值）

适用于同一批采集结果内部的去重，以及和历史数据库的去重
"""

from difflib import SequenceMatcher
from typing import List

from storage.models import RawNewsItem
from storage.database import exists_batch
from utils.logger import get_logger

logger = get_logger(__name__)

# 标题相似度阈值（超过此值视为重复）
SIMILARITY_THRESHOLD = 0.80


def _title_similarity(title1: str, title2: str) -> float:
    """计算两个标题的相似度"""
    # 标准化：去空格、小写
    t1 = " ".join(title1.lower().split())
    t2 = " ".join(title2.lower().split())
    return SequenceMatcher(None, t1, t2).ratio()


def dedup_in_batch(items: List[RawNewsItem]) -> List[RawNewsItem]:
    """
    同一批次内部去重
    策略: 标题相似度 > SIMILARITY_THRESHOLD 且来自不同源，保留 authority_score 更高的
    """
    if len(items) <= 1:
        return items

    kept = []
    for item in items:
        is_dup = False
        for i, existing in enumerate(kept):
            sim = _title_similarity(item.title, existing.title)
            if sim >= SIMILARITY_THRESHOLD:
                is_dup = True
                # 如果新条目信源更权威，替换旧条目
                if item.authority_score > existing.authority_score:
                    kept[i] = item
                    logger.debug(
                        f"替换去重: '{existing.title[:40]}...' "
                        f"(sim={sim:.2f}) -> 更权威信源"
                    )
                else:
                    logger.debug(
                        f"标题去重: '{item.title[:40]}...' "
                        f"(sim={sim:.2f}) 跳过"
                    )
                break

        if not is_dup:
            kept.append(item)

    logger.info(f"批内去重: {len(items)} -> {len(kept)} 条")
    return kept


def dedup_against_history(items: List[RawNewsItem]) -> List[RawNewsItem]:
    """
    与数据库历史记录去重
    剔除已采集过的 URL
    """
    if not items:
        return items

    urls = [item.url for item in items]
    existing_urls = exists_batch(urls)

    filtered = [item for item in items if item.url not in existing_urls]

    skipped = len(items) - len(filtered)
    if skipped > 0:
        logger.info(f"历史去重: 跳过 {skipped} 条已采集")

    return filtered
