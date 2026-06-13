"""
数据源定义

所有 RSS 源、Google News 搜索词、中文网页采集目标
每个数据源包含名称、URL、类型、语言、信源权威等级
"""

SOURCES = {
    # ══════════════════════════════════════════════════════════
    # Google News RSS — 关键词搜索（覆盖面最广）
    # ══════════════════════════════════════════════════════════
    "google_news": {
        "type": "google_news",
        "authority_level": "C",  # 聚合来源，权威度中等
        "authority_score": 6,
        "searches": [
            # 综合创新
            "food beverage innovation trend",
            "food industry new product launch",
            # 植物基 / 替代蛋白
            "plant based food innovation",
            "alternative protein new product",
            # 可持续包装
            "sustainable food packaging innovation",
            # 食品科技
            "food tech AI digital innovation",
            # 融资并购
            "food startup funding acquisition IPO",
            # 从媒体名单补充 — 细分赛道
            "dairy innovation new product",
            "beverage innovation coffee tea",
            "functional food nutrition health",
            "food ingredient innovation clean label",
        ],
    },
    "google_news_cn": {
        "type": "google_news",
        "authority_level": "C",
        "authority_score": 6,
        "language": "zh-CN",
        "country": "CN",
        "searches": [
            "食品 饮料 创新 新品",
            "食品行业 融资 收购",
            "植物基 替代蛋白 食品",
            "食品科技 数字化 智能制造",
        ],
    },

    # ══════════════════════════════════════════════════════════
    # 国际行业媒体 RSS
    # ══════════════════════════════════════════════════════════
    "food_dive": {
        "type": "rss",
        "url": "https://www.fooddive.com/feeds/news/",
        "name": "Food Dive",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "food_navigator": {
        "type": "rss",
        "url": "https://www.foodnavigator.com/Info/RSS",
        "name": "Food Navigator",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "bevnet": {
        "type": "rss",
        "url": "https://www.bevnet.com/rss",
        "name": "BevNET",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "just_food": {
        "type": "rss",
        "url": "https://www.just-food.com/feed/",
        "name": "Just Food",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "food_business_news": {
        "type": "rss",
        "url": "https://www.foodbusinessnews.net/rss",
        "name": "Food Business News",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "beverage_daily": {
        "type": "rss",
        "url": "https://www.beveragedaily.com/Info/RSS",
        "name": "Beverage Daily",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "food_ingredients_first": {
        "type": "rss",
        "url": "https://www.foodingredientsfirst.com/rss",
        "name": "Food Ingredients First",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },

    # ══════════════════════════════════════════════════════════
    # 国际媒体 — 从媒体名单补充（食品细分赛道）
    # ══════════════════════════════════════════════════════════
    "foodbev": {
        "type": "rss",
        "url": "https://www.foodbev.com/feed/",
        "name": "FoodBev Media",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "dairy_reporter": {
        "type": "rss",
        "url": "https://www.dairyreporter.com/Info/RSS",
        "name": "Dairy Reporter",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "nutrition_insight": {
        "type": "rss",
        "url": "https://www.nutritioninsight.com/Info/RSS",
        "name": "Nutrition Insight",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
    },
    "green_queen": {
        "type": "rss",
        "url": "https://www.greenqueen.com.hk/feed/",
        "name": "Green Queen",
        "language": "en",
        "authority_level": "A",
        "authority_score": 9,
    },
    "vegconomist": {
        "type": "rss",
        "url": "https://vegconomist.com/feed/",
        "name": "Vegconomist",
        "language": "en",
        "authority_level": "A",
        "authority_score": 9,
        "enabled": False,  # 纯素商业，按需开启
    },
    "the_spoon": {
        "type": "rss",
        "url": "https://thespoon.tech/feed/",
        "name": "The Spoon",
        "language": "en",
        "authority_level": "A",
        "authority_score": 9,
        "enabled": False,  # 食品科技专项
    },

    # ══════════════════════════════════════════════════════════
    # 中文行业媒体 — 网页采集（从媒体名单补充）
    # ══════════════════════════════════════════════════════════
    "foodtalks": {
        "type": "web",
        "url": "https://www.foodtalks.cn/news",
        "name": "FoodTalks",
        "language": "zh",
        "authority_level": "A",
        "authority_score": 9,
        "article_selector": "div.news-item",   # 待调试确认
        "title_selector": "a.title",
        "link_selector": "a.title",
    },
    "fbif": {
        "type": "web",
        "url": "https://www.foodtalks.cn/fbif",
        "name": "FBIF 食品饮料创新",
        "language": "zh",
        "authority_level": "A",
        "authority_score": 9,
        "article_selector": "div.article-item",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
    },
    "foodmate": {
        "type": "web",
        "url": "https://news.foodmate.net/",
        "name": "食品伙伴网",
        "language": "zh",
        "authority_level": "A",
        "authority_score": 9,
        "article_selector": "div.newslist li, ul.catlist li",
        "title_selector": "a",
        "link_selector": "a",
    },
    "xiaoshidai": {
        "type": "web",
        "url": "https://www.xiaoshidai.com/",
        "name": "小食代",
        "language": "zh",
        "authority_level": "B",
        "authority_score": 8,
        "article_selector": "article, div.post-item",
        "title_selector": "h2 a, h3 a, a.title",
        "link_selector": "h2 a, h3 a, a.title",
    },
    "36kr_food": {
        "type": "web",
        "url": "https://36kr.com/newsflashes",
        "name": "36氪快讯",
        "language": "zh",
        "authority_level": "B",
        "authority_score": 8,
        "article_selector": "div.newsflash-item, div.item-desc",
        "title_selector": "a.item-title, span.title",
        "link_selector": "a",
        "enabled": False,  # 需要验证 CSS selector
    },

    # ══════════════════════════════════════════════════════════
    # 综合商业媒体（可选补充）
    # ══════════════════════════════════════════════════════════
    "reuters_food": {
        "type": "rss",
        "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best&best-sectors=food-beverage",
        "name": "Reuters Food",
        "language": "en",
        "authority_level": "S",
        "authority_score": 10,
        "enabled": False,  # Reuters RSS 可能受限
    },

    # ══════════════════════════════════════════════════════════
    # 社交媒体 — LinkedIn 公司+KOL
    # ══════════════════════════════════════════════════════════
    "linkedin": {
        "type": "linkedin",
        "name": "LinkedIn",
        "language": "en",
        "authority_level": "D",       # 社交媒体，权威度较低
        "authority_score": 4,
        "enabled": True,              # 需要 .env 中配置 LINKEDIN_EMAIL + PASSWORD
    },
}

# ── Google News 的 hl/gl/ceid 默认参数 ──
GOOGLE_NEWS_PARAMS = {
    "hl": "en-US",
    "gl": "US",
    "ceid": "US:en",
}

GOOGLE_NEWS_PARAMS_CN = {
    "hl": "zh-CN",
    "gl": "CN",
    "ceid": "CN:zh",
}
