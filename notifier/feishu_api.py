"""
飞书开放平台 API 个人推送

使用飞书 App Bot 向指定用户发送消息（无需群聊）
流程: App ID + Secret → tenant_access_token → 发送消息 API

参考文档: https://open.feishu.cn/document/server-docs/im-v1/message/create
"""

import json
import time
from typing import Optional

import requests

from config.settings import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    FEISHU_USER_OPEN_ID,
    REQUEST_TIMEOUT,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# 飞书 API 端点
TOKEN_URL = (
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
)
SEND_MSG_URL = (
    "https://open.feishu.cn/open-apis/im/v1/messages"
    "?receive_id_type=open_id"
)

# Token 缓存（用于复用，避免每次请求都获取）
_token_cache = {"token": None, "expires_at": 0}


def _get_tenant_access_token() -> Optional[str]:
    """
    获取 tenant_access_token（带缓存，有效期约 2 小时）

    Returns:
        token 字符串，失败返回 None
    """
    global _token_cache

    # 缓存有效则直接返回
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        logger.error("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置")
        return None

    try:
        resp = requests.post(
            TOKEN_URL,
            json={
                "app_id": FEISHU_APP_ID,
                "app_secret": FEISHU_APP_SECRET,
            },
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        data = resp.json()

        if data.get("code") != 0:
            logger.error(f"获取 token 失败: code={data.get('code')}, msg={data.get('msg')}")
            return None

        token = data["tenant_access_token"]
        expire = data.get("expire", 7200)  # 默认 2 小时

        _token_cache = {
            "token": token,
            "expires_at": time.time() + expire,
        }

        logger.debug(f"获取 tenant_access_token 成功")
        return token

    except Exception as e:
        logger.error(f"获取 token 异常: {e}")
        return None


def send_message_to_user(payload: dict) -> bool:
    """
    通过飞书 API 向指定用户发送消息

    Args:
        payload: 消息体，格式同 webhook 的 interactive card
                 包含 msg_type 和 card 字段

    Returns:
        是否发送成功
    """
    if not FEISHU_USER_OPEN_ID:
        logger.error("FEISHU_USER_OPEN_ID 未配置，无法发送个人消息")
        return False

    token = _get_tenant_access_token()
    if not token:
        return False

    # 飞书 API 发送消息时，interactive 类型的 content 必须是 JSON 字符串
    msg_type = payload.get("msg_type", "interactive")

    if msg_type == "interactive":
        card_data = payload.get("card", {})
        content = json.dumps(card_data, ensure_ascii=False)
        body = {
            "receive_id": FEISHU_USER_OPEN_ID,
            "msg_type": "interactive",
            "content": content,
        }
    elif msg_type == "text":
        text_content = payload.get("content", {}).get("text", "")
        body = {
            "receive_id": FEISHU_USER_OPEN_ID,
            "msg_type": "text",
            "content": json.dumps({"text": text_content}, ensure_ascii=False),
        }
    else:
        logger.error(f"不支持的 msg_type: {msg_type}")
        return False

    # 重试发送
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                SEND_MSG_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIMEOUT,
            )
            result = resp.json()
            code = result.get("code", -1)
            msg = result.get("msg", "")

            if code == 0:
                logger.info("飞书个人消息发送成功")
                return True
            else:
                logger.warning(
                    f"发送失败 (尝试 {attempt}/3): code={code}, msg={msg}"
                )

                # Token 过期则刷新重试
                if code in (99991663, 99991664, 99991668, 99991671):
                    _token_cache["token"] = None
                    token = _get_tenant_access_token()
                    if not token:
                        return False
                else:
                    return False

        except requests.Timeout:
            logger.warning(f"请求超时 (尝试 {attempt}/3)")
        except Exception as e:
            logger.error(f"发送异常: {e}")

        if attempt < 3:
            time.sleep(2)

    logger.error("飞书个人消息发送失败，已重试 3 次")
    return False


def send_test_message() -> bool:
    """发送一条测试消息，验证飞书 App 配置"""
    payload = {
        "msg_type": "text",
        "content": {
            "text": (
                "✅ 食品饮料创新热点监测系统\n\n"
                "飞书个人推送配置验证成功！\n"
                "每日早 9:00 将自动推送热点日报到你的飞书。\n\n"
                f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        },
    }
    return send_message_to_user(payload)
