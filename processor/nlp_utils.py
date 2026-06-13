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


# ── 食品相关性门禁 ──────────────────────────
# 文本中必须包含至少一个关键词，否则判定为非食品内容，直接丢弃
FOOD_GATE_KEYWORDS = [
    # 中文 — 基础
    "食品", "饮料", "饮品", "零食", "餐饮", "食材", "配料",
    "乳品", "乳制品", "烘焙", "面包", "蛋糕", "糖果", "巧克力",
    # 中文 — 品类
    "茶饮", "咖啡", "奶茶", "气泡水", "预制菜", "速食", "方便面",
    "自热", "冷冻食品", "速冻", "奶酪", "酸奶", "牛奶", "鲜奶",
    "冰淇淋", "饼干", "坚果", "薯片", "肉干", "卤味",
    # 中文 — 行业
    "食品行业", "食品产业", "食业", "快消", "FMCG", "新消费",
    "酒", "啤酒", "白酒", "葡萄酒", "调味品", "食用油",
    "肉制品", "水产", "农产品", "饮料行业", "乳业", "糖酒",
    # 英文 — 基础
    "food", "beverage", "drink", "snack", "dairy", "bakery",
    "grocery", "confectionery", "brew", "brewery", "distill",
    # 英文 — 品类
    "coffee", "tea", "soda", "juice", "water", "wine", "beer",
    "spirit", "milk", "cheese", "yogurt", "butter", "cream",
    "bread", "cake", "pastry", "cookie", "cracker", "biscuit",
    "chocolate", "candy", "chips", "nut", "meat", "poultry",
    "seafood", "plant-based", "protein", "ingredient",
    # 英文 — 公司/品牌
    "nestle", "pepsico", "coca-cola", "unilever", "danone",
    "mondelez", "mars", "generalmills", "kraft", "heinz",
    "tyson", "beyond meat", "oatly", "starbucks", "mcdonald",
    "kfc", "burger king", "subway", "domino", "yili", "mengniu",
]


def is_food_related(text: str) -> bool:
    """检查文本是否与食品饮料相关"""
    text_lower = text.lower()
    for kw in FOOD_GATE_KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False


def detect_priority_category(text: str) -> Tuple[str, float]:
    """
    检测文本是否匹配六大优先品类

    返回: (品类名, 加分值) — 未匹配返回 ("", 0)
    """
    from config.keywords import PRIORITY_CATEGORIES

    text_lower = text.lower()
    best_boost = 0.0
    best_label = ""

    for cat_key, cat_data in PRIORITY_CATEGORIES.items():
        boost = cat_data["boost"]

        # 中文关键词
        for kw in cat_data["zh_keywords"]:
            if kw.lower() in text_lower:
                if boost > best_boost:
                    best_boost = boost
                    best_label = cat_data["label"]
                break
        else:
            # 英文关键词
            for kw in cat_data["en_keywords"]:
                try:
                    if re.search(kw, text_lower, re.IGNORECASE):
                        if boost > best_boost:
                            best_boost = boost
                            best_label = cat_data["label"]
                        break
                except re.error:
                    pass

    return (best_label, best_boost)
