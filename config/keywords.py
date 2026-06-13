"""
食品饮料行业关键词库
- 公司名映射（用于 NER 识别）
- 创新关键词（用于分类和评分）
"""

# ════════════════════════════════════════════════════════════
# 公司名称映射（含别称、英文名、股票代码等）
# 供 jieba 自定义词典和关键词匹配使用
# ════════════════════════════════════════════════════════════

COMPANY_TIERS = {
    # Tier 1: 全球巨头 (得分 10)
    "tier1": {
        "score": 10,
        "companies": [
            # 中文名, 英文名/别称
            ("雀巢", "Nestlé"),
            ("百事", "PepsiCo"),
            ("可口可乐", "Coca-Cola"),
            ("联合利华", "Unilever"),
            ("达能", "Danone"),
            ("亿滋", "Mondelez"),
            ("百威英博", "AB InBev"),
            ("卡夫亨氏", "Kraft Heinz"),
            ("玛氏", "Mars"),
            ("通用磨坊", "General Mills"),
            ("三得利", "Suntory"),
            ("麒麟", "Kirin"),
        ],
    },
    # Tier 2: 国际重要 (得分 8)
    "tier2": {
        "score": 8,
        "companies": [
            ("费列罗", "Ferrero"),
            ("明治", "Meiji"),
            ("味之素", "Ajinomoto"),
            ("丘比", "Kewpie"),
            ("金宝汤", "Campbell Soup"),
            ("荷美尔", "Hormel"),
            ("泰森", "Tyson Foods"),
            ("Beyond Meat", "Beyond Meat"),
            ("Oatly", "Oatly"),
            ("Impossible Foods", "Impossible Foods"),
            ("家乐氏", "Kellogg's"),
            ("好时", "Hershey"),
            ("帝亚吉欧", "Diageo"),
            ("保乐力加", "Pernod Ricard"),
        ],
    },
    # Tier 3: 中国龙头 (得分 9)
    "tier3": {
        "score": 9,
        "companies": [
            ("蒙牛", "Mengniu"),
            ("伊利", "Yili"),
            ("农夫山泉", "Nongfu Spring"),
            ("海天", "Haitian"),
            ("康师傅", "Master Kong"),
            ("统一", "Uni-President"),
            ("旺旺", "Want Want"),
            ("双汇", "Shuanghui"),
            ("飞鹤", "Feihe"),
            ("光明乳业", "Bright Dairy"),
            ("安井", "Anjoy"),
            ("三全", "Sanquan"),
            ("桃李面包", "Toly Bread"),
            ("金龙鱼", "Jinlongyu"),
        ],
    },
    # Tier 4: 中国新锐 (得分 7)
    "tier4": {
        "score": 7,
        "companies": [
            ("元气森林", "Genki Forest"),
            ("喜茶", "Heytea"),
            ("瑞幸", "Luckin Coffee"),
            ("奈雪", "Nayuki"),
            ("认养一头牛", "Renyang Yitouniu"),
            ("简爱", "Jane Love"),
            ("每日黑巧", "Chocday"),
            ("ffit8", "ffit8"),
            ("王饱饱", "Wangbaobao"),
            ("官栈", "Guanzhan"),
            ("鲨鱼菲特", "Shark Fit"),
            ("三只松鼠", "Three Squirrels"),
            ("良品铺子", "Bestore"),
            ("来伊份", "Laiyifen"),
            ("卫龙", "Weilong"),
            ("自嗨锅", "Zihaiguo"),
            ("空刻", "AirMeter"),
            ("茶颜悦色", "Sexy Tea"),
            ("蜜雪冰城", "Mixue"),
            ("霸王茶姬", "Chagee"),
        ],
    },
}

# ── 扁平化公司查找表 ──
# 格式: {"关键词": ("标准名", 得分)}
COMPANY_LOOKUP = {}
for tier_key, tier_data in COMPANY_TIERS.items():
    for names in tier_data["companies"]:
        for name in names:
            normalized = name.lower().strip()
            COMPANY_LOOKUP[normalized] = (names[0], tier_data["score"])


# ════════════════════════════════════════════════════════════
# 创新关键词（用于创新相关性分类和评分）
# ════════════════════════════════════════════════════════════

INNOVATION_KEYWORDS = {
    # 新品发布 / 产品创新 (得分 10)
    "product_launch": {
        "score": 10,
        "label": "产品创新",
        "zh_patterns": [
            "新品上市", "新品发布", "新品首发", "全新上市", "全新推出",
            "推出全新", "新产品", "新系列", "正式上市", "正式发售",
            "上市发布", "首发", "限定款", "季节限定", "创新产品",
            "新口味", "新配方", "升级版", "全新.*上市",
        ],
        "en_patterns": [
            r"new\s+product", r"launch(es|ed|ing)?", r"roll.?out",
            r"unveil(s|ed|ing)?", r"debut(s|ed|ing)?",
            r"introduc(es|ed|ing)?", r"new\s+flavo(u)?r",
            r"limited\s+edition", r"new\s+line",
        ],
    },
    # 原料 / 配方创新 (得分 10)
    "ingredient": {
        "score": 10,
        "label": "原料创新",
        "zh_patterns": [
            "新原料", "替代蛋白", "植物基", "植物蛋白", "细胞培养",
            "发酵技术", "合成生物", "精准营养", "功能性成分",
            "益生菌", "后生元", "益生元", "膳食纤维", "代糖",
            "减糖", "减盐", "减脂", "清洁标签", "clean label",
            "天然色素", "天然防腐", "无添加", "零添加",
        ],
        "en_patterns": [
            r"plant.?based", r"alternative\s+protein", r"cell.?based",
            r"cultivated\s+meat", r"fermentation",
            r"clean\s+label", r"functional\s+ingredient",
            r"probiotic", r"prebiotic", r"postbiotic",
            r"sugar\s+reduction", r"salt\s+reduction",
            r"upcycl(ed|ing)", r"novel\s+ingredient",
        ],
    },
    # 包装 / 可持续创新 (得分 9)
    "packaging_sustainability": {
        "score": 9,
        "label": "包装/可持续",
        "zh_patterns": [
            "可回收", "可降解", "生物基包装", "减塑", "无标签",
            "碳中和", "碳足迹", "可持续发展", "ESG", "循环经济",
            "再生材料", "环保包装", "轻量化", "重复使用", "纸基包装",
        ],
        "en_patterns": [
            r"sustainable", r"recycl(able|ed)", r"biodegradable",
            r"compostable", r"carbon\s+neutral", r"net\s+zero",
            r"circular\s+economy", r"eco.?friendly",
            r"plastic.?free", r"refill(able)?", r"reusable",
            r"rPET", r"mono.?material",
        ],
    },
    # 技术 / 数字化 (得分 8)
    "technology": {
        "score": 8,
        "label": "技术/数字化",
        "zh_patterns": [
            "人工智能", "AI", "机器学习", "数字化", "智能制造",
            "数字孪生", "区块链", "物联网", "智慧工厂", "工业4.0",
            "自动化", "大数据", "云计算", "AR", "VR",
            "精准发酵", "3D打印", "食品科技",
        ],
        "en_patterns": [
            r"\bAI\b", r"artificial\s+intelligence", r"machine\s+learning",
            r"digital\s+twin", r"blockchain", r"smart\s+manufacturing",
            r"automation", r"food\s+tech", r"3D\s+print(ed|ing)",
            r"precision\s+fermentation", r"IoT",
        ],
    },
    # 融资 / IPO / 收购 (得分 7)
    "funding_ma": {
        "score": 7,
        "label": "投融资/收购",
        "zh_patterns": [
            "融资", "A轮", "B轮", "C轮", "D轮", "IPO", "上市",
            "收购", "并购", "投资", "估值", "亿元", "千万元",
            "股权", "Pre-IPO", "天使轮", "种子轮",
        ],
        "en_patterns": [
            r"fund(ing|raise)", r"series\s+[A-D]", r"IPO",
            r"acquis?i(tion|re)", r"merger?", r"invest(ment|or)?",
            r"valu(ation|ed\s+at)", r"\$\d+[\s]?[BM]",
        ],
    },
    # 渠道 / 商业模式 (得分 6)
    "channel_biz": {
        "score": 6,
        "label": "渠道/模式",
        "zh_patterns": [
            "DTC", "D2C", "直面消费者", "全渠道", "私域", "直播带货",
            "抖音", "快手", "拼多多", "社区团购", "会员制", "订阅制",
            "新零售", "即时零售", "前置仓",
        ],
        "en_patterns": [
            r"DTC", r"D2C", r"direct.?to.?consumer",
            r"omnichannel", r"subscription", r"e.?commerce",
            r"quick\s+commerce", r"dark\s+store",
        ],
    },
    # 市场营销 (得分 5)
    "marketing": {
        "score": 5,
        "label": "市场营销",
        "zh_patterns": [
            "品牌升级", "品牌焕新", "代言人", "品牌大使",
            "跨界联名", "IP联名", "品牌campaign", "营销案例",
            "TVC", "social营销", "话题营销",
        ],
        "en_patterns": [
            r"rebrand(ing)?", r"brand\s+refresh", r"campaign",
            r"collaboration", r"partnership", r"ambassador",
            r"influencer", r"marketing",
        ],
    },
}

# 非创新类/降权关键词（得分 3）
ROUTINE_KEYWORDS = {
    "score": 3,
    "label": "常规动态",
    "zh_patterns": [
        "季度财报", "年报", "业绩报告", "人事任命", "人事调动",
        "工厂投产", "生产基地", "经销商大会", "股东大会",
        "投资者关系", "股东会", "董事会",
    ],
    "en_patterns": [
        r"quarterly\s+earnings?", r"annual\s+report",
        r"board\s+of\s+directors", r"appointment",
        r"financial\s+results?", r"shareholder",
    ],
}

# ════════════════════════════════════════════════════════════
# 优先品类关键词 — 六大核心赛道
# 匹配到则获得额外评分加成
# ════════════════════════════════════════════════════════════

PRIORITY_CATEGORIES = {
    "beverage": {
        "label": "饮料",
        "boost": 1.0,  # 额外加分
        "zh_keywords": [
            "饮料", "饮品", "气泡水", "碳酸饮料", "果汁", "茶饮",
            "奶茶", "咖啡", "即饮", "RTD", "功能饮料", "能量饮料",
            "植物奶", "燕麦奶", "椰奶", "豆奶", "杏仁奶",
            "冷萃", "冷泡", "现制茶饮", "新茶饮", "瓶装水",
            "矿泉水", "苏打水", "电解质", "运动饮料", "乳酸菌饮料",
            "冰茶", "凉茶", "即饮咖啡", "即饮茶",
            "可口可乐", "百事", "农夫山泉", "元气森林", "喜茶",
            "瑞幸", "蜜雪冰城", "星巴克", "东方树叶", "三得利",
            "红牛", "魔爪", "燃茶", "外星人", "王老吉",
        ],
        "en_keywords": [
            "beverage", "drink", "sparkling water", "soda",
            "juice", "tea", "coffee", "ready-to-drink", "RTD",
            "energy drink", "functional drink", "plant milk",
            "oat milk", "almond milk", "coconut milk",
            "cold brew", "bubble tea", "soft drink",
            "electrolyte", "sports drink", "bottled water",
            "Starbucks", "Coca-Cola", "PepsiCo", "Monster",
            "Red Bull", "Suntory", "Lipton",
        ],
    },
    "instant_food": {
        "label": "速食",
        "boost": 1.0,
        "zh_keywords": [
            "速食", "方便食品", "方便面", "方便米饭", "方便粉",
            "自热", "即食", "冲泡", "速冻", "微波炉", "冷冻食品",
            "料理包", "速食粥", "速食汤", "拉面", "螺蛳粉",
            "酸辣粉", "拌面", "杯面", "碗面", "冻干",
            "康师傅", "统一", "今麦郎", "自嗨锅", "拉面说",
        ],
        "en_keywords": [
            "instant food", "instant noodle", "ramen",
            "ready meal", "instant rice", "frozen food",
            "microwave meal", "freeze-dried", "cup noodle",
            "convenience food", "instant soup", "self-heating",
        ],
    },
    "prepared_meals": {
        "label": "预制菜",
        "boost": 1.0,
        "zh_keywords": [
            "预制菜", "半成品菜", "即烹", "即热", "即配",
            "净菜", "中央厨房", "调理食品", "快手菜", "预制食品",
            "到家", "美团", "叮咚", "盒马", "山姆",
        ],
        "en_keywords": [
            "prepared meal", "meal kit", "ready-to-cook",
            "ready-to-heat", "pre-cooked", "semi-prepared",
            "central kitchen", "heat-and-eat", "cook-at-home",
            "delivery meal kit", "pre-made meal",
        ],
    },
    "dairy": {
        "label": "乳品",
        "boost": 1.0,
        "zh_keywords": [
            "乳品", "乳制品", "牛奶", "酸奶", "奶酪", "黄油",
            "奶油", "奶粉", "炼乳", "冰淇淋", "雪糕", "奶盖",
            "常温奶", "鲜奶", "低温奶", "巴氏奶", "A2",
            "高蛋白奶", "零乳糖", "乳饮料", "含乳",
            "蒙牛", "伊利", "光明", "君乐宝", "认养一头牛",
            "简爱", "乐纯", "妙可蓝多", "百吉福", "安佳",
        ],
        "en_keywords": [
            "dairy", "milk", "yogurt", "cheese", "butter",
            "cream", "ice cream", "whey", "lactose",
            "A2 milk", "protein milk", "fresh milk",
            "UHT milk", "skim milk", "whole milk",
            "Danone", "Yili", "Mengniu", "Arla",
            "Fonterra", "Lactalis", "Nestlé dairy",
            "dairy alternative", "cheese innovation",
        ],
    },
    "bakery": {
        "label": "烘焙",
        "boost": 1.0,
        "zh_keywords": [
            "烘焙", "面包", "蛋糕", "饼干", "糕点", "甜点",
            "吐司", "欧包", "法棍", "可颂", "丹麦", "贝果",
            "马卡龙", "蛋挞", "曲奇", "蛋卷", "威化",
            "预烘焙", "冷冻面团", "现烤", "短保", "长保",
            "桃李", "达利", "好丽友", "奥利奥", "宾堡",
            "幸福西饼", "鲍师傅", "泸溪河", "冠生园",
        ],
        "en_keywords": [
            "bakery", "bread", "cake", "cookie", "pastry",
            "biscuit", "cracker", "toast", "baguette",
            "croissant", "bagel", "donut", "muffin",
            "sourdough", "gluten-free bakery", "artisan bread",
            "frozen dough", "par-baked", "fresh baked",
            "Oreo", "Mondelez", "Grupo Bimbo", "Yamazaki",
        ],
    },
    "snacks": {
        "label": "零食",
        "boost": 1.0,
        "zh_keywords": [
            "零食", "休闲食品", "小吃", "膨化", "薯片", "坚果",
            "果干", "蜜饯", "糖果", "巧克力", "肉干", "肉脯",
            "豆干", "海苔", "爆米花", "虾条", "卤味",
            "代餐", "蛋白棒", "能量棒", "每日坚果", "混合坚果",
            "三只松鼠", "良品铺子", "来伊份", "百草味", "洽洽",
            "卫龙", "盐津铺子", "劲仔", "玛氏", "亿滋",
            "费列罗", "好时", "雀巢", "旺旺", "上好佳",
        ],
        "en_keywords": [
            "snack", "snacking", "savory snack", "chips",
            "crisps", "nuts snack", "dried fruit", "jerky",
            "chocolate", "candy", "confectionery", "popcorn",
            "protein bar", "granola bar", "trail mix",
            "seaweed snack", "puffed snack", "biscuit",
            "Mars Wrigley", "Mondelez", "Hershey", "Ferrero",
            "PepsiCo snacks", "Kellogg snack",
        ],
    },
}

# ── jieba 自定义词典词条 ──
# 确保食品行业专有名词不被错误切分
JIEBA_CUSTOM_WORDS = []
for tier_data in COMPANY_TIERS.values():
    for names in tier_data["companies"]:
        for name in names:
            JIEBA_CUSTOM_WORDS.append(name)

# 额外添加一些行业专有名词
JIEBA_CUSTOM_WORDS.extend([
    "植物基", "清洁标签", "后生元", "益生元", "益生菌",
    "替代蛋白", "植物蛋白", "细胞培养肉", "合成生物学",
    "精准发酵", "碳中和", "碳足迹", "元气森林", "认养一头牛",
    "自嗨锅", "茶颜悦色", "蜜雪冰城", "霸王茶姬", "三只松鼠",
    "良品铺子", "每日黑巧", "鲨鱼菲特", "王饱饱",
])
