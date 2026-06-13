"""
SQLite 数据库封装
- 存储历史新闻，用于去重和回溯
- 提供增删查接口
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import List, Optional

from config.settings import DATABASE_PATH
from storage.models import ScoredNewsItem
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source_name TEXT,
            language TEXT,
            summary TEXT,
            published_at TEXT,
            collected_at TEXT NOT NULL,
            authority_score INTEGER,
            company_score INTEGER,
            company_name TEXT,
            innovation_score INTEGER,
            innovation_label TEXT,
            recency_score INTEGER,
            buzz_score INTEGER,
            total_score REAL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 索引用於快速查重和日誌查詢
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_url_hash
        ON news_history(url_hash)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collected_at
        ON news_history(collected_at)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_total_score
        ON news_history(total_score DESC)
    """)

    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {DATABASE_PATH}")


def url_to_hash(url: str) -> str:
    """对 URL 进行 SHA256 哈希"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def exists(url: str) -> bool:
    """检查某 URL 是否已经采集过"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM news_history WHERE url_hash = ? LIMIT 1",
        (url_to_hash(url),),
    )
    result = cursor.fetchone() is not None
    conn.close()
    return result


def exists_batch(urls: List[str]) -> set:
    """批量检查 URL 是否存在，返回已存在的 URL 集合"""
    if not urls:
        return set()
    conn = _get_connection()
    cursor = conn.cursor()
    hashes = [url_to_hash(u) for u in urls]
    placeholders = ",".join(["?"] * len(hashes))
    cursor.execute(
        f"SELECT url FROM news_history WHERE url_hash IN ({placeholders})",
        hashes,
    )
    existing = {row["url"] for row in cursor.fetchall()}
    conn.close()
    return existing


def insert(news_item: ScoredNewsItem):
    """插入一条已评分的新闻"""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO news_history
                (url_hash, title, url, source_name, language, summary,
                 published_at, collected_at, authority_score, company_score,
                 company_name, innovation_score, innovation_label,
                 recency_score, buzz_score, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url_to_hash(news_item.url),
                news_item.title,
                news_item.url,
                news_item.source_name,
                news_item.language,
                news_item.summary,
                news_item.published_at.isoformat() if news_item.published_at else None,
                news_item.collected_at.isoformat(),
                news_item.authority_score,
                news_item.company_score,
                news_item.company_name,
                news_item.innovation_score,
                news_item.innovation_label,
                news_item.recency_score,
                news_item.buzz_score,
                news_item.total_score,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # 重复 URL，忽略
    finally:
        conn.close()


def insert_batch(items: List[ScoredNewsItem]):
    """批量插入已评分的新闻"""
    conn = _get_connection()
    cursor = conn.cursor()
    inserted = 0
    for item in items:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO news_history
                    (url_hash, title, url, source_name, language, summary,
                     published_at, collected_at, authority_score, company_score,
                     company_name, innovation_score, innovation_label,
                     recency_score, buzz_score, total_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url_to_hash(item.url),
                    item.title,
                    item.url,
                    item.source_name,
                    item.language,
                    item.summary,
                    item.published_at.isoformat() if item.published_at else None,
                    item.collected_at.isoformat(),
                    item.authority_score,
                    item.company_score,
                    item.company_name,
                    item.innovation_score,
                    item.innovation_label,
                    item.recency_score,
                    item.buzz_score,
                    item.total_score,
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    logger.debug(f"批量插入: {inserted}/{len(items)} 条新记录")


def get_today_headlines(limit: int = 20) -> List[dict]:
    """获取今天的头条（按评分降序）"""
    conn = _get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT * FROM news_history
        WHERE collected_at LIKE ?
        ORDER BY total_score DESC
        LIMIT ?
        """,
        (f"{today}%", limit),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def clean_old_records(days: int = 30):
    """清理 N 天前的旧记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM news_history
        WHERE collected_at < datetime('now', '-' || ? || ' days')
        """,
        (days,),
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"清理旧记录: 删除 {deleted} 条")
