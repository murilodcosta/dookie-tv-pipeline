"""
SQLite Database interface for recording video history, costs, Cloudflare R2 links, and enforcing the 7-day topic/mascot no-repeat rule.
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
        """Initializes SQLite tables and performs migrations if needed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    mascot TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    r2_url TEXT,
                    r2_key TEXT,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES video_history (id)
                );
            """)

            # Auto-migration check for existing databases
            cursor.execute("PRAGMA table_info(video_history);")
            columns = [col[1] for col in cursor.fetchall()]
            if "description" not in columns:
                cursor.execute("ALTER TABLE video_history ADD COLUMN description TEXT;")
            if "r2_url" not in columns:
                cursor.execute("ALTER TABLE video_history ADD COLUMN r2_url TEXT;")
            if "r2_key" not in columns:
                cursor.execute("ALTER TABLE video_history ADD COLUMN r2_key TEXT;")

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
        Selects a mascot and topic respecting round-robin mascot rotation and the 7-day no-repeat rule.
        """
        if override_mascot:
            target_mascot = override_mascot
        else:
            # Query last used mascot from video_history to rotate (dookie -> mia -> carrot -> dookie)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT mascot FROM video_history ORDER BY id DESC LIMIT 1;")
                row = cursor.fetchone()
                if row and row[0] in available_mascots:
                    last_mascot = row[0]
                    last_idx = available_mascots.index(last_mascot)
                    target_mascot = available_mascots[(last_idx + 1) % len(available_mascots)]
                else:
                    target_mascot = available_mascots[0]

        for topic in available_topics:
            if self.is_topic_valid_for_mascot(topic, target_mascot):
                return target_mascot, topic

        # Fallback if all topics were used recently
        return target_mascot, available_topics[0]

    def log_video(
        self,
        topic: str,
        mascot: str,
        title: str,
        status: str,
        description: Optional[str] = None,
        r2_url: Optional[str] = None,
        r2_key: Optional[str] = None,
        youtube_url: Optional[str] = None,
    ) -> int:
        """Logs a generated video entry into SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO video_history (topic, mascot, title, description, status, r2_url, r2_key, youtube_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (topic, mascot, title, description, status, r2_url, r2_key, youtube_url),
            )
            conn.commit()
            return cursor.lastrowid

    def log_metrics(self, video_id: int, estimated_cost: float, views_24h: int = 0, views_7d: int = 0):
        """Logs cost observability metrics linked to a specific video."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics_log (video_id, estimated_cost, views_24h, views_7d)
                VALUES (?, ?, ?, ?)
                """,
                (video_id, estimated_cost, views_24h, views_7d),
            )
            conn.commit()
            logger.info(f"📊 Observability logged for Video #{video_id}: Estimated Cost = ${estimated_cost:.4f}")
