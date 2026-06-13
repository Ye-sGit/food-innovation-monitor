"""
飞书消息发送模块 — 统一入口

支持两种模式:
- webhook: 群自定义机器人（签名验签 → POST Webhook URL）
- api:     个人推送（App Bot API → tenant_access_token → 发送消息）

根据 FEISHU_MODE 配置自动选择
"""

import time
import hmac
import hashlib
import base64

import requests

from config.settings import (
    FEISHU_MODE,
    FEISHU_WEBHOOK_URL,
    FEISHU_WEBHOOK_SECRET,
    REQUEST_TIMEOUT,
)
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


# ═══════════════════════════════════════════════
# Webhook 模式 — HMAC-SHA256 签名
# ═══════════════════════════════════════════════

def generate_sign(timestamp: str = None) -> tuple[str, str]:
    """生成飞书签名校验所需的 timestamp 和 sign"""
    if timestamp is None:
        timestamp = str(int(time.time()))

    if not FEISHU_WEBHOOK_SECRET:
        return timestamp, ""

    string_to_sign = f"{timestamp}\n{FEISHU_WEBHOOK_SECRET}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")
    return timestamp, sign


def _send_via_webhook(payload: dict) -> bool:
    """通过群机器人 Webhook 发送"""
    if not FEISHU_WEBHOOK_URL:
        logger.error("FEISHU_WEBHOOK_URL 未配置")
        return False

    timestamp, sign = generate_sign()
    payload["timestamp"] = timestamp
    payload["sign"] = sign

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                FEISHU_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            result = resp.json()
            code = result.get("code", -1)
            msg = result.get("msg", "")

            if code == 0:
                logger.info("飞书 Webhook 发送成功")
                return True

            logger.warning(
                f"Webhook 发送失败 (尝试 {attempt}/{MAX_RETRIES}): "
                f"code={code}, msg={msg}"
            )

            if code in (19021, 19022, 19024):  # 不可重试的错误
                return False

        except requests.Timeout:
            logger.warning(f"请求超时 (尝试 {attempt}/{MAX_RETRIES})")
        except Exception as e:
            logger.error(f"发送异常: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    logger.error(f"Webhook 发送失败，已重试 {MAX_RETRIES} 次")
    return False


# ═══════════════════════════════════════════════
# API 模式 — App Bot 个人推送
# ═══════════════════════════════════════════════

def _send_via_api(payload: dict) -> bool:
    """通过飞书 App Bot API 发送个人消息"""
    from notifier.feishu_api import send_message_to_user
    return send_message_to_user(payload)


# ═══════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════

def send_message(payload: dict) -> bool:
    """
    发送消息到飞书（根据 FEISHU_MODE 自动选择通道）

    Args:
        payload: 消息体（webhook 和 api 通用格式）
                 interactive 卡片: {"msg_type": "interactive", "card": {...}}
                 文本消息:        {"msg_type": "text", "content": {"text": "..."}}

    Returns:
        是否发送成功
    """
    if FEISHU_MODE == "api":
        logger.info("使用飞书 API 模式（个人推送）")
        return _send_via_api(payload)
    else:
        logger.info("使用飞书 Webhook 模式（群机器人）")
        return _send_via_webhook(payload)


def send_test_message() -> bool:
    """发送测试消息，验证飞书配置"""
    payload = {
        "msg_type": "text",
        "content": {
            "text": (
                "✅ 食品饮料创新热点监测系统\n\n"
                "飞书配置验证成功！系统已就绪。\n"
                f"推送模式: {'个人推送 (API)' if FEISHU_MODE == 'api' else '群机器人 (Webhook)'}\n"
                f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        },
    }
    return send_message(payload)
