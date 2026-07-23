"""
SQLite Database interface for recording video history, costs, and enforcing the 7-day topic/mascot no-repeat rule.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "data/pipeline.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initializes SQLite tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    mascot TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    youtube_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    views_24h INTEGER DEFAULT 0,
                    views_7d INTEGER DEFAULT 0,
                    estimated_cost REAL DEFAULT 0.0,
                    FOREIGN KEY (video_id) REFERENCES video_history (id)
                );
            """)
            conn.commit()

    def is_topic_valid_for_mascot(self, topic: str, mascot: str, days: int = 7) -> bool:
        """
        Enforces the 7-day no-repeat rule: returns True if topic was NOT used for the mascot within the last `days` days.
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM video_history
                WHERE topic = ? AND mascot = ? AND created_at >= ? AND status = 'approved'
                """,
                (topic, mascot, cutoff_date),
            )
            count = cursor.fetchone()[0]
            return count == 0

    def select_next_mascot_and_topic(
        self, available_topics: List[str], available_mascots: List[str], override_mascot: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Selects a mascot and topic respecting the 7-day no-repeat rule, with optional manual override.
        """
        target_mascot = override_mascot if override_mascot else available_mascots[0]
        
        for topic in available_topics:
            if self.is_topic_valid_for_mascot(topic, target_mascot):
                return target_mascot, topic

        # Fallback if all topics were used recently
        return target_mascot, available_topics[0]

    def log_video(self, topic: str, mascot: str, title: str, status: str, youtube_url: Optional[str] = None) -> int:
        """Logs a generated video entry into SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO video_history (topic, mascot, title, status, youtube_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (topic, mascot, title, status, youtube_url),
            )
            conn.commit()
            return cursor.lastrowid
