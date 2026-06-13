"""
NLP 工具模块
- jieba 分词初始化（加载自定义食品行业词典）
- 公司名识别
- 中英文关键词匹配
"""

import re
from typing import Optional, Tuple

import jieba

from config.keywords import (
    COMPANY_LOOKUP,
    JIEBA_CUSTOM_WORDS,
    INNOVATION_KEYWORDS,
    ROUTINE_KEYWORDS,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ── 初始化 jieba ──────────────────────────────
_jieba_initialized = False


def init_jieba():
    """初始化 jieba 分词（加载自定义词典）"""
    global _jieba_initialized
    if _jieba_initialized:
        return

    for word in JIEBA_CUSTOM_WORDS:
        jieba.add_word(word)

    _jieba_initialized = True
    logger.info(f"jieba 初始化完成，已加载 {len(JIEBA_CUSTOM_WORDS)} 个自定义词条")


# ── 公司名匹配 ────────────────────────────────


def find_companies(text: str) -> list:
    """
    在文本中查找匹配的公司名
    返回 [(标准名, 得分), ...] 列表，按得分降序排列
    """
    text_lower = text.lower()
    found = {}

    for keyword, (standard_name, score) in COMPANY_LOOKUP.items():
        if keyword in text_lower:
            if standard_name not in found or score > found[standard_name]:
                found[standard_name] = score

    # 按得分降序排列
    result = sorted(found.items(), key=lambda x: x[1], reverse=True)
    return result


def get_top_company(text: str) -> Tuple[str, int]:
    """
    获取文本中最重要的一个公司
    返回 (公司名, 得分)，默认返回 ("其他", 5)
    """
    companies = find_companies(text)
    if companies:
        return companies[0]
    return ("其他", 5)


# ── 关键词匹配（通用） ────────────────────────


def _keyword_match(text: str, patterns: list) -> bool:
    """检查文本是否匹配任一模式（支持正则和普通子串匹配）"""
    text_lower = text.lower()
    for pattern in patterns:
        # 如果是正则表达式模式（以 r 开头的字符串无法直接判断，用编译尝试）
        try:
            if re.search(pattern, text_lower):
                return True
        except re.error:
            # 不是正则，当作普通子串匹配
            if pattern.lower() in text_lower:
                return True
    return False


# ── 创新分类 ──────────────────────────────────


def classify_innovation(text: str, language: str = "zh") -> Tuple[int, str]:
    """
    对文本进行创新相关性分类
    返回 (得分, 标签)

    策略：
    1. 先检查是否为常规动态（财报/人事），如果是则给低分
    2. 遍历创新关键词库，取最高匹配得分
    3. 无匹配则默认给 5 分
    """
    text_lower = text.lower()

    # 先检查是否为常规降权内容
    routine_matched = False
    for pattern in ROUTINE_KEYWORDS["zh_patterns"]:
        if pattern.lower() in text_lower:
            routine_matched = True
            break
    for pattern in ROUTINE_KEYWORDS["en_patterns"]:
        try:
            if re.search(pattern, text_lower):
                routine_matched = True
                break
        except re.error:
            pass

    if routine_matched:
        return (ROUTINE_KEYWORDS["score"], ROUTINE_KEYWORDS["label"])

    # 遍历创新关键词库
    best_score = 5  # 默认中性得分
    best_label = "行业动态"
    best_priority = 0  # 定义创新类型的优先级

    # 按创新类型优先级遍历（得分高的先匹配）
    sorted_categories = sorted(
        INNOVATION_KEYWORDS.items(),
        key=lambda x: x[1]["score"],
        reverse=True,
    )

    for category_key, category_data in sorted_categories:
        score = category_data["score"]
        label = category_data["label"]

        # 中文匹配
        if language in ("zh", "zh-CN"):
            for pattern in category_data["zh_patterns"]:
                if pattern.lower() in text_lower:
                    if score > best_score:
                        best_score = score
                        best_label = label
                    break
            else:
                # 中文没匹配到，继续检查英文
                for pattern in category_data["en_patterns"]:
                    try:
                        if re.search(pattern, text_lower):
                            if score > best_score:
                                best_score = score
                                best_label = label
                            break
                    except re.error:
                        pass
                continue
            # 匹配到了，跳出外层循环
            if best_score == score:
                break

        # 英文匹配（或中文+英文混合）
        if language in ("en",):
            for pattern in category_data["en_patterns"]:
                try:
                    if re.search(pattern, text_lower):
                        if score > best_score:
                            best_score = score
                            best_label = label
                        break
                except re.error:
                    pass
            else:
                for pattern in category_data["zh_patterns"]:
                    if pattern.lower() in text_lower:
                        if score > best_score:
                            best_score = score
                            best_label = label
                        break
                continue
            if best_score == score:
                break

    return (best_score, best_label)
