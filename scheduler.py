"""
后台常驻定时调度器（睡眠版 — 适应 PIN 登录）

使用 APScheduler，每日 09:00 运行采集→评分→推送流程。
推送后: 空闲 → 睡眠（非关机）；有人用 → 继续运行。

睡眠期间，APScheduler 会在唤醒后立即补跑（misfire_grace_time=2h）。

配合 Windows 闹钟/唤醒定时器使用:
  - 推送后将电脑转入睡眠（省电，无需密码登录）
  - 需要额外设置一个每天 08:55 的唤醒任务（见 setup_wake_timer.ps1）
"""

import sys
import os
import time
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta

# ⚠️ 开机启动时 CWD 不是项目目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = __import__("pathlib").Path(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from main import run_daily
from processor.nlp_utils import init_jieba
from storage.database import init_db
from utils.logger import get_logger

logger = get_logger("scheduler")

# ── 空闲检测 ────────────────────────────────

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def get_idle_seconds() -> float:
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        return 999
    return max(0, (ctypes.windll.kernel32.GetTickCount64() - lii.dwTime) / 1000.0)


def maybe_sleep():
    """
    推送后判断:
    - 用户空闲 > 5 分钟 → 进入睡眠（省电，唤醒后无需密码）
    - 用户正在使用 → 不睡，继续后台等明天
    """
    idle = get_idle_seconds()
    logger.info(f"推送后检测: 用户空闲 {idle:.0f} 秒 ({idle/60:.1f} 分钟)")
    if idle < 300:
        logger.info("用户仍在使用电脑 → 不睡眠，继续后台运行")
        return

    logger.info("用户已离开 → 30 秒后进入睡眠（无需密码即可唤醒）")
    # 睡眠命令: 强制休眠，禁止唤醒定时器之外的唤醒源
    subprocess.run(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"],
        timeout=10,
    )
    # 从睡眠恢复后继续
    logger.info("系统已从睡眠恢复，继续后台运行")


# ── 调度逻辑 ────────────────────────────────

def scheduled_job():
    """每日 9:00 触发的任务"""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"\n{'='*50}")
    logger.info(f"⏰ 定时触发 — {now_str}")
    logger.info(f"{'='*50}")
    try:
        run_daily()
    except Exception as e:
        logger.error(f"任务异常: {e}", exc_info=True)
    else:
        maybe_sleep()


def main():
    # 初始化
    init_jieba()
    init_db()

    # 后台调度器
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_food_news",
        name="食品饮料创新热点日报",
        replace_existing=True,
        misfire_grace_time=7200,  # 唤醒后 2 小时内补跑
    )
    scheduler.start()

    logger.info("=" * 50)
    logger.info("🍽️  食品创新热点 — 睡眠版后台常驻")
    logger.info("=" * 50)
    logger.info(f"启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("调度: 每日 09:00 | 推送后空闲→睡眠 | 唤醒→自动补跑")
    logger.info("=" * 50)

    # 检查今天是否需要补跑
    now = datetime.now()
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= today_9am:
        today_log = PROJECT_PATH / "logs" / f"monitor-{now.strftime('%Y-%m-%d')}.log"
        already_ran = (
            today_log.exists()
            and "推送状态" in today_log.read_text(encoding="utf-8", errors="ignore")
        )
        if not already_ran:
            logger.info("⚠️ 检测到今天 9:00 已过且未运行，立即补跑...")
            scheduled_job()

    # 持续运行（睡眠会暂停这个循环，唤醒后自动继续）
    logger.info("后台运行中，等待每日 09:00 触发...")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        logger.info("收到停止信号，退出。")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
