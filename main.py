"""
主入口 — 单次运行：采集 → 处理 → 评分 → 推送

用法:
    python main.py            # 运行完整流程
    python main.py --test     # 只发送测试消息（验证飞书配置）
    python main.py --dry-run  # 只采集和评分，不发送飞书消息
"""

import sys
import time
from datetime import datetime

from config.settings import TOP_IMPORTANT_COUNT, TOP_SECONDARY_COUNT
from config.sources import SOURCES

from collectors.rss_collector import RssCollector
from collectors.google_news import GoogleNewsCollector
from collectors.web_collector import WebCollector
from collectors.linkedin_collector import LinkedInCollector

from processor.nlp_utils import init_jieba
from processor.dedup import dedup_in_batch, dedup_against_history
from processor.ranker import rank_items, split_top_items

from notifier.feishu_card import build_daily_card, build_error_card
from notifier.feishu_sender import send_message, send_test_message

from storage.database import init_db, insert_batch, clean_old_records
from storage.models import RawNewsItem

from utils.logger import get_logger

logger = get_logger("main")

# 采集器类型映射
COLLECTOR_MAP = {
    "rss": RssCollector,
    "google_news": GoogleNewsCollector,
    "web": WebCollector,
    "linkedin": LinkedInCollector,
}


def collect_all() -> list[RawNewsItem]:
    """
    从所有数据源采集新闻
    返回 RawNewsItem 列表
    """
    all_items = []
    logger.info("=" * 50)
    logger.info("🚀 开始采集食品饮料创新热点...")
    logger.info("=" * 50)

    for source_key, source_config in SOURCES.items():
        source_type = source_config.get("type", "")
        enabled = source_config.get("enabled", True)

        if not enabled:
            logger.debug(f"跳过禁用的数据源: {source_key}")
            continue

        collector_cls = COLLECTOR_MAP.get(source_type)
        if collector_cls is None:
            logger.warning(f"未知的采集器类型: {source_type} ({source_key})")
            continue

        try:
            collector = collector_cls(source_config)
            items = collector.fetch()
            all_items.extend(items)
        except Exception as e:
            logger.error(f"采集器异常 [{source_key}]: {e}", exc_info=True)
            continue

    logger.info(f"\n📊 总共采集: {len(all_items)} 条原始新闻")
    return all_items


def process_pipeline(raw_items: list[RawNewsItem]) -> tuple:
    """
    处理流水线: 去重 → 评分 → 排序 → 分组

    Returns:
        (top_items, secondary_items, total_scored)
    """
    logger.info("\n" + "─" * 50)
    logger.info("🔧 开始处理流水线...")

    # Step 1: 与历史数据库去重
    items = dedup_against_history(raw_items)
    logger.info(f"Step 1 历史去重后: {len(items)} 条")

    # Step 2: 批内去重
    items = dedup_in_batch(items)
    logger.info(f"Step 2 批内去重后: {len(items)} 条")

    # Step 2.5: 食品相关性门禁（非食品内容直接丢掉）
    from processor.nlp_utils import is_food_related
    before = len(items)
    items = [it for it in items if is_food_related(it.title + " " + it.summary)]
    if before > len(items):
        logger.info(f"Step 2.5 食品门禁过滤: {before - len(items)} 条非食品内容")

    # Step 3: 多因子评分 + 排序
    scored = rank_items(items)
    logger.info(f"Step 3 评分完成: {len(scored)} 条")

    # Step 4: 分组
    top_items, secondary_items = split_top_items(
        scored,
        top_n=TOP_IMPORTANT_COUNT,
        secondary_n=TOP_SECONDARY_COUNT,
    )
    logger.info(
        f"Step 4 分组: 最重要 {len(top_items)} 条, "
        f"次重要 {len(secondary_items)} 条"
    )

    # Step 5: 存入数据库
    insert_batch(scored)
    clean_old_records(days=30)

    return top_items, secondary_items, len(scored)


def run_daily():
    """每日运行入口"""
    start_time = time.time()

    try:
        # 1. 初始化
        init_jieba()
        init_db()

        # 2. 采集
        raw_items = collect_all()

        if not raw_items:
            logger.warning("未采集到任何新闻，跳过推送")
            # 发送空结果通知
            card = build_error_card("今日未采集到任何新闻，请检查网络或数据源是否正常。")
            send_message(card)
            return

        # 3. 处理
        top_items, secondary_items, total_scored = process_pipeline(raw_items)

        # 4. 构建飞书卡片
        card = build_daily_card(
            top_items,
            secondary_items,
            total_collected=len(raw_items),
        )

        # 5. 发送飞书消息
        success = send_message(card)

        elapsed = time.time() - start_time
        logger.info(f"\n✅ 日报流程完成 ({elapsed:.1f}s)")
        logger.info(
            f"   推送状态: {'成功 ✓' if success else '失败 ✗'}"
        )

    except Exception as e:
        logger.error(f"运行异常: {e}", exc_info=True)

        # 发送错误通知
        try:
            error_card = build_error_card(str(e))
            send_message(error_card)
        except Exception:
            pass


def run_dry():
    """干跑模式：只采集+评分，不推送"""
    init_jieba()
    init_db()

    raw_items = collect_all()
    if not raw_items:
        logger.warning("未采集到任何新闻")
        return

    top_items, secondary_items, total_scored = process_pipeline(raw_items)

    logger.info("\n" + "=" * 50)
    logger.info("📋 干跑结果预览（不推送）:")
    logger.info("=" * 50)

    for i, item in enumerate(top_items, 1):
        logger.info(
            f"  {i:2d}. [{item.total_score:.1f}] {item.innovation_label} | "
            f"{item.company_name:10s} | {item.title[:60]}..."
        )

    if secondary_items:
        logger.info(f"\n  ... 还有 {len(secondary_items)} 条次重要热点")


def main():
    """命令入口"""
    args = sys.argv[1:]
    mode = args[0] if args else "run"

    if mode == "--test":
        logger.info("发送飞书测试消息...")
        success = send_test_message()
        logger.info(f"结果: {'成功 ✓' if success else '失败 ✗'}")
        if not success:
            logger.error(
                "请检查: 1) .env 中 FEISHU_WEBHOOK_URL 是否正确 "
                "2) 是否开启了签名校验但未配置 FEISHU_WEBHOOK_SECRET "
                "3) 是否开启了 IP 白名单 "
                "4) 是否设置了关键词过滤"
            )
    elif mode == "--dry-run":
        run_dry()
    else:
        run_daily()


if __name__ == "__main__":
    main()
