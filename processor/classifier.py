"""
创新相关性分类器

封装分类逻辑，提供批量处理接口
"""

from typing import List

from storage.models import RawNewsItem
from processor.nlp_utils import classify_innovation, get_top_company
from utils.logger import get_logger

logger = get_logger(__name__)


def classify_batch(items: List[RawNewsItem]) -> list:
    """
    对一批 RawNewsItem 进行分类处理
    返回 [(item, innovation_score, innovation_label, company_name, company_score), ...]
    """
    results = []

    for item in items:
        # 创新分类
        innov_score, innov_label = classify_innovation(
            item.title + " " + item.summary,
            item.language,
        )

        # 公司识别
        company_name, company_score = get_top_company(
            item.title + " " + item.summary,
        )

        results.append({
            "item": item,
            "innovation_score": innov_score,
            "innovation_label": innov_label,
            "company_name": company_name,
            "company_score": company_score,
        })

    return results
