"""
飞书消息卡片构造器

将评分排序后的新闻列表格式化为飞书 interactive message card
卡片包含:
- 蓝色头部（日期 + 统计信息）
- 🔥 最重要热点区域（Top 10）
- 📌 次重要热点区域（Next 10）
- 底部按钮和页脚
"""

from datetime import datetime
from typing import List

from storage.models import ScoredNewsItem
from config.settings import TOP_IMPORTANT_COUNT, TOP_SECONDARY_COUNT
from utils.logger import get_logger

logger = get_logger(__name__)

# 飞书卡片颜色映射
HEADER_COLOR = "blue"

# 评分 emoji 区间映射
def score_badge(score: float) -> str:
    """根据总分返回对应的 emoji 标识"""
    if score >= 9.0:
        return "🟢"
    elif score >= 8.0:
        return "🔵"
    elif score >= 7.0:
        return "🟡"
    elif score >= 6.0:
        return "🟠"
    else:
        return "⚪"


def _format_time(published_at: datetime | None) -> str:
    """格式化发布时间为相对时间描述"""
    if published_at is None:
        return "未知时间"

    now = datetime.now()
    if published_at.tzinfo is None:
        delta = now - published_at
    else:
        from datetime import timezone
        delta = now.astimezone(timezone.utc) - published_at

    hours = delta.total_seconds() / 3600

    if hours < 1:
        return f"{int(delta.total_seconds() / 60)} 分钟前"
    elif hours < 24:
        return f"{int(hours)} 小时前"
    else:
        days = int(hours / 24)
        return f"{days} 天前"


def _build_news_section(
    items: List[ScoredNewsItem],
    section_title: str,
    start_index: int = 1,
) -> str:
    """
    构建一个新闻条目区块的 markdown 文本

    格式:
    🔥 **最重要的 10 个热点**
    ---
    1. [9.2] 🟢 新闻标题...
       🏷️ 产品创新 · 🏭 Nestlé · 📰 Food Dive · ⏰ 3小时前
       [查看原文](url)
    ---
    """
    lines = [f"**{section_title}**\n"]

    for i, item in enumerate(items):
        idx = start_index + i
        badge = score_badge(item.total_score)
        title = item.title[:80]
        if len(item.title) > 80:
            title += "..."

        # 标题行
        lines.append(f"{idx}\\. [{item.total_score:.1f}] {badge} {title}")

        # 标签行
        tags = []
        tags.append(f"🏷️ {item.innovation_label}")
        if item.company_name != "其他":
            tags.append(f"🏭 {item.company_name}")
        tags.append(f"📰 {item.source_name}")
        tags.append(f"⏰ {_format_time(item.published_at)}")

        lines.append(f"　{' · '.join(tags)}")

        # 摘要（如果有）
        if item.summary:
            summary = item.summary[:100]
            if len(item.summary) > 100:
                summary += "..."
            lines.append(f"　> {summary}")

        # 链接
        lines.append(f"　[查看原文]({item.url})")

        # 分割线（最后一条不加）
        if i < len(items) - 1:
            lines.append("")
        else:
            lines.append("\n---")

    return "\n".join(lines)


def build_daily_card(
    top_items: List[ScoredNewsItem],
    secondary_items: List[ScoredNewsItem],
    total_collected: int,
) -> dict:
    """
    构建每日热点日报的飞书 interactive card

    Args:
        top_items: 最重要热点 (Top 10)
        secondary_items: 次重要热点 (Next 10)
        total_collected: 总共采集的新闻条数

    Returns:
        飞书 interactive card JSON payload
    """
    today = datetime.now().strftime("%Y年%m月%d日")
    total_selected = len(top_items) + len(secondary_items)

    # 构建卡片 elements
    elements = []

    # ── 顶部概览 ──
    overview_text = (
        f"共采集 **{total_collected}** 条行业资讯，"
        f"精选 **{total_selected}** 条核心热点\n"
        f"推送时间: {datetime.now().strftime('%H:%M')}"
    )
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": overview_text,
        },
    })
    elements.append({"tag": "hr"})

    # ── 最重要热点 ──
    if top_items:
        top_section = _build_news_section(
            top_items,
            f"🔥 最重要的 {len(top_items)} 个热点",
            start_index=1,
        )
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": top_section,
            },
        })
    else:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "🔥 **最重要的热点**\n\n暂无数据，请稍后再试。",
            },
        })

    # ── 次重要热点 ──
    if secondary_items:
        sec_section = _build_news_section(
            secondary_items,
            f"📌 次重要热点 ({len(secondary_items)} 条)",
            start_index=len(top_items) + 1,
        )
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": sec_section,
            },
        })

    elements.append({"tag": "hr"})

    # ── 底部说明 ──
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": (
                "🤖 由 **Food Innovation Monitor** 自动生成\n"
                "⏰ 每日 09:00 定时推送\n"
                f"📊 评分算法: 信源权威20% + 公司重要15% + "
                f"创新相关25% + 时效25% + 热度15% | "
                f"仅推送48小时内热点"
            ),
        },
    })

    # ── 按钮 ──
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "🔍 查看数据来源"},
                "type": "default",
                "url": "https://github.com/IceLand/food-innovation-monitor/blob/main/README.md",
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📊 评分算法说明"},
                "type": "default",
                "url": "https://github.com/IceLand/food-innovation-monitor/blob/main/README.md",
            },
        ],
    })

    # ── 组装完整卡片 ──
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": HEADER_COLOR,
                "title": {
                    "tag": "plain_text",
                    "content": f"🍽️ 食品饮料创新热点日报 · {today}",
                },
            },
            "elements": elements,
        },
    }

    logger.info(
        f"卡片构建完成: Top {len(top_items)} + Second {len(secondary_items)} 条, "
        f"总采集 {total_collected} 条"
    )

    return card


def build_error_card(error_msg: str) -> dict:
    """构建错误通知卡片（采集异常时发送）"""
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": "red",
                "title": {
                    "tag": "plain_text",
                    "content": "⚠️ 食品创新热点监测异常",
                },
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**错误信息:**\n"
                            f"```\n{error_msg}\n```\n\n"
                            f"⏰ 发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"系统将自动重试下一次采集。"
                        ),
                    },
                },
            ],
        },
    }
