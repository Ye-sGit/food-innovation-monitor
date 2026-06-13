# 🍽️ Food Innovation Monitor — 食品饮料创新热点监测 + 飞书自动推送

覆盖国内外头部食品公司动态，通过**多因子重要性排序算法**筛选热点，
每日早 9:00 通过飞书机器人自动推送到飞书群。

---

## ✨ 功能特色

- 🌍 **多源采集** — RSS（国际行业媒体）+ Google News 关键词搜索 + 中文媒体网页抓取 + LinkedIn（可选）
- 🧠 **智能评分** — 五因子加权算法：信源权威度 + 公司重要性 + 创新相关性 + 时效性 + 热度信号
- 📊 **精选推送** — 每日筛选 🔥最重要 10 条 + 📌次重要 10 条
- 💬 **飞书卡片** — 精美的 interactive card 格式，支持 Markdown、链接跳转
- ⏰ **定时任务** — 每日 09:00 自动运行，支持 Windows/macOS/Linux
- 🗄️ **历史存储** — SQLite 存储 + 自动去重 + 30 天自动清理

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- 飞书账号

### 2. 安装依赖

```bash
cd food-innovation-monitor
pip install -r requirements.txt
```

### 3. 选择推送方式

两种方式二选一：

| 方式 | 适用场景 | 复杂度 |
|------|---------|--------|
| **群机器人 Webhook** | 推送到群聊，多人可见 | ⭐ 简单 |
| **个人推送 API** | 私密推送到个人飞书 | ⭐⭐ 需创建应用 |

---

#### 方式 A：个人推送（推荐 ↑）

通过飞书应用直接给你个人发消息，无需群聊。

**3A.1 创建飞书应用**

1. 打开 [飞书开发者后台](https://open.feishu.cn/app) → **创建应用** → 选**企业自建应用**
2. 应用名称填 `食品热点监测`，上传头像
3. 进入应用设置页 → **添加应用能力** → 添加 **机器人**
4. 在**凭证与基础信息**页面，复制：
   - **App ID**（格式：`cli_xxxxxxxxxxxx`）
   - **App Secret**（点击"复制"）
5. 在左侧菜单 **安全设置** 中，添加 `127.0.0.1` 到 IP 白名单（本机测试用）
6. 点击右上角 **创建版本** → **申请线上发布**（仅自己可见，无需审批）

**3A.2 获取你的用户 Open ID**

1. 飞书开发者后台 → 左侧菜单 **用户管理**（或访问 `https://open.feishu.cn/app` → 你的应用 → 用户管理）
2. 找到你自己的飞书账号 → 复制 **Open ID**（格式：`ou_xxxxxxxxxxxx`）
3. 或者在应用设置页 → **事件与回调** → 搜索你的飞书名也能看到 Open ID

**3A.3 添加机器人为联系人**

1. 打开飞书 App → 搜索栏输入你的应用名 `食品热点监测`
2. 点击搜索结果中的应用 → 进入对话 → 发送任意消息（如 "hi"）
3. 这样就激活了机器人对话通道

**3A.4 填写配置**

编辑 `.env`：
```env
FEISHU_MODE=api
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=你的APP_SECRET
FEISHU_USER_OPEN_ID=ou_xxxxxxxxxxxx
```

---

#### 方式 B：群机器人 Webhook

**3B.1 创建机器人**

1. 打开飞书 → 进入目标群 → **群设置 → 群机器人 → 添加自定义机器人**
2. 复制 **Webhook URL** 和 **Secret**

**3B.2 填写配置**

编辑 `.env`：
```env
FEISHU_MODE=webhook
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的URL
FEISHU_WEBHOOK_SECRET=你的Secret
```

---

### 4. 测试验证

```bash
# 测试飞书连接（发送测试消息）
python main.py --test
```

收到 "✅ 配置验证成功" = 搞定。

### 5. 手动运行一次

```bash
# 完整运行（采集→评分→推送）
python main.py

# 干跑模式（只采集评分，不推送）
python main.py --dry-run
```

### 6. 启动定时任务

```bash
# 后台运行，每天 09:00 自动推送
python scheduler.py

# 立即运行一次
python scheduler.py --once
```

---

## 📁 项目结构

```
food-innovation-monitor/
├── config/                      # 配置
│   ├── settings.py              # 全局配置（Webhook、路径等）
│   ├── sources.py               # 数据源定义
│   └── keywords.py              # 关键词库 + 公司映射
├── collectors/                  # 采集器
│   ├── rss_collector.py         # RSS 采集
│   ├── google_news.py           # Google News 采集
│   ├── web_collector.py         # 网页采集
│   └── linkedin_collector.py    # LinkedIn 采集（可选）
├── processor/                   # 处理器
│   ├── nlp_utils.py             # NLP 工具（jieba 分词）
│   ├── classifier.py            # 创新分类器
│   ├── dedup.py                 # 去重
│   └── ranker.py                # 多因子评分
├── notifier/                    # 通知
│   ├── feishu_card.py           # 飞书卡片构造
│   └── feishu_sender.py         # 签名 + 发送
├── storage/                     # 存储
│   ├── models.py                # 数据模型
│   └── database.py              # SQLite 操作
├── utils/
│   └── logger.py                # 日志
├── data/                        # 数据库文件（自动创建）
├── logs/                        # 日志文件（自动创建）
├── main.py                      # 手动运行入口
├── scheduler.py                 # 定时任务入口
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📊 评分算法

| 因子 | 权重 | 说明 |
|------|------|------|
| 信源权威度 | 25% | S级(10): Food Dive, Reuters → D级(4): 社交 |
| 公司重要性 | 20% | Tier1(10): 雀巢/百事 → Tier5(5): 其他 |
| 创新相关性 | 30% | 产品创新(10) → 常规财报(3) |
| 时效性 | 15% | <6h(10) → >48h(0) |
| 热度信号 | 10% | 暂用默认值5（后续可扩展） |

---

## 📡 数据源

### 国际媒体（RSS）
- Food Dive, Food Navigator, BevNET, Just Food
- Food Business News, Beverage Daily, Food Ingredients First

### 中文媒体（网页采集）
- FoodTalks, FBIF, 食品伙伴网, 小食代

### Google News RSS
- 中英文关键词搜索，覆盖范围最广

### LinkedIn（可选）
- 默认关闭，需在 `.env` 配置 LinkedIn 账号

---

## ⚙️ 高级配置

### 修改推送时间

编辑 `scheduler.py`，修改 `CronTrigger(hour=9, minute=0)` 中的时间。

### 添加/删除数据源

编辑 `config/sources.py`：
- 添加新 RSS 源：新增 `"type": "rss"` 的条目
- 添加新搜索词：在 `google_news.searches` 数组追加

### 调整评分权重

编辑 `processor/ranker.py` 中的 `WEIGHTS` 字典。

### 添加监控公司

编辑 `config/keywords.py` 中的 `COMPANY_TIERS`，添加公司名（中文+英文别名）。

---

## 🐛 常见问题

| 问题 | 解决方案 |
|------|---------|
| 飞书消息发送失败 `code=19021` | 签名校验失败，检查 Secret 是否正确（注意不要有多余空格） |
| 飞书消息发送失败 `code=19024` | 消息中未包含设置的关键词，在卡片 header 中已默认包含"食品" |
| 采集结果为空 | 检查网络连接；部分 RSS 可能需要代理 |
| LinkedIn 登录失败 | 已自动跳过 LinkedIn 采集；如需使用请检查账号密码 |
| 网页采集无结果 | 目标网站可能更新了 CSS 选择器，需调试 `selectors` |

---

## 📝 License

MIT
