"""
开机自启单次运行脚本 — 省电版

逻辑:
1. 启动后等待到当天 09:00
2. 执行采集 → 评分 → 飞书推送
3. 推送完毕后:
   - 检测用户是否在操作电脑（鼠标/键盘）
   - 超过 5 分钟无人操作 → 自动关机省电
   - 检测到有人使用 → 不关机，只退出程序
"""

import sys
import os
import time
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta

# ⚠️ 关键: 开机启动时 CWD 不是项目目录，必须手动设置 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from processor.nlp_utils import init_jieba
from storage.database import init_db
from main import collect_all, process_pipeline
from notifier.feishu_card import build_daily_card, build_error_card
from notifier.feishu_sender import send_message
from utils.logger import get_logger

logger = get_logger("daily_task")

# ── Windows 用户空闲检测 ────────────────────

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def get_idle_seconds() -> float:
    """获取用户空闲时间（秒）"""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        return 999
    tick = ctypes.windll.kernel32.GetTickCount64()
    return max(0, (tick - lii.dwTime) / 1000.0)


def should_shutdown(idle_threshold: int = 300) -> bool:
    """
    判断是否应该关机：用户空闲超过阈值
    """
    try:
        idle = get_idle_seconds()
        logger.info(f"检测用户空闲时长: {idle:.0f} 秒 ({idle/60:.1f} 分钟)")
        if idle >= idle_threshold:
            logger.info(f"用户已离开 {idle/60:.1f} 分钟 → 准备关机")
            return True
        else:
            logger.info(f"用户仍在使用电脑 → 不关机，直接退出")
            return False
    except Exception as e:
        logger.warning(f"空闲检测失败: {e}，不关机")
        return False


def do_shutdown():
    """执行 Windows 关机（60 秒倒计时，可取消）"""
    logger.info("系统将在 60 秒后关机...")
    logger.info("如需取消，请在 60 秒内运行: shutdown /a")
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", "60", "/c", "食品热点推送完成，即将关机"],
            capture_output=True,
            timeout=10,
        )
    except Exception as e:
        logger.error(f"关机命令失败: {e}")


# ── 主逻辑 ──────────────────────────────────

def wait_until_9am():
    """等待到最近一个上午 9:00"""
    now = datetime.now()
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)

    if now >= target:
        target += timedelta(days=1)

    wait_seconds = (target - now).total_seconds()
    hours = wait_seconds / 3600

    logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"等待 {hours:.1f} 小时到 {target.strftime('%Y-%m-%d %H:%M')} 后执行...")

    while wait_seconds > 0:
        sleep_chunk = min(wait_seconds, 3600)
        time.sleep(sleep_chunk)
        wait_seconds -= sleep_chunk
        if wait_seconds > 0:
            logger.info(f"  还剩 {wait_seconds/3600:.1f} 小时...")

    logger.info("到达 9:00 执行时间！")


def main():
    """入口"""
    logger.info("=" * 50)
    logger.info("📋 食品创新热点 - 开机自启（省电模式）")
    logger.info("=" * 50)

    # 1. 等到 9 点
    wait_until_9am()

    # 2. 初始化
    init_jieba()
    init_db()

    # 3. 执行日报流程（到点就执行，不等人离开）
    start_time = time.time()

    try:
        raw_items = collect_all()

        if not raw_items:
            logger.warning("未采集到任何新闻")
        else:
            top_items, secondary_items, _ = process_pipeline(raw_items)
            card = build_daily_card(top_items, secondary_items, len(raw_items))
            send_message(card)

        elapsed = time.time() - start_time
        logger.info(f"✅ 推送完成 ({elapsed:.1f}s)")

    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        try:
            send_message(build_error_card(str(e)))
        except Exception:
            pass

    # 4. 判断是否关机
    if should_shutdown(idle_threshold=300):
        do_shutdown()
    # 否则直接退出，不关电脑

    logger.info("程序退出。\n")


if __name__ == "__main__":
    main()
