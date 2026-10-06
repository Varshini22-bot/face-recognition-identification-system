"""
SQLite database for attendance records.
"""
import os
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Optional


class Database:
    """Manages attendance records in a local SQLite database."""

    def __init__(self, db_path: str = "data/attendance.db"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._init()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT    NOT NULL,
                    similarity REAL   NOT NULL DEFAULT 0,
                    timestamp TEXT    NOT NULL,
                    photo     TEXT
                )
                """
            )
            c.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_attendance(
        self, name: str, similarity: float, photo: Optional[str] = None
    ):
        with self._conn() as c:
            c.execute(
                "INSERT INTO attendance (name, similarity, timestamp, photo) VALUES (?, ?, ?, ?)",
                (name, round(similarity, 4), datetime.now().isoformat(timespec="seconds"), photo),
            )
            c.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_attendance(
        self,
        limit: int = 100,
        date_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        if date_filter:
            query += " AND timestamp LIKE ?"
            params.append(f"{date_filter}%")
        if name_filter:
            query += " AND name = ?"
            params.append(name_filter)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._conn() as c:
            rows = c.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        today = date.today().isoformat()
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
            today_all = c.execute(
                "SELECT COUNT(*) FROM attendance WHERE timestamp LIKE ?", (f"{today}%",)
            ).fetchone()[0]
            unique_today = c.execute(
                "SELECT COUNT(DISTINCT name) FROM attendance "
                "WHERE timestamp LIKE ? AND name != 'unknown'",
                (f"{today}%",),
            ).fetchone()[0]
            unknown_today = c.execute(
                "SELECT COUNT(*) FROM attendance "
                "WHERE timestamp LIKE ? AND name = 'unknown'",
                (f"{today}%",),
            ).fetchone()[0]
        return {
            "total": total,
            "today": today_all,
            "unique_today": unique_today,
            "unknown_today": unknown_today,
        }
