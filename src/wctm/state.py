"""SQLite persistence layer for watches, ticket checks, and notifications."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from wctm.models import TicketStatus, UserWatch

_SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
    match_id TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    last_notified TEXT,
    notify_email INTEGER NOT NULL DEFAULT 1,
    notify_desktop INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ticket_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    available INTEGER NOT NULL,
    categories TEXT NOT NULL DEFAULT '[]',
    price_range TEXT,
    checked_at TEXT NOT NULL,
    ticket_url TEXT
);

CREATE TABLE IF NOT EXISTS notifications_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    sent_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ticket_checks_match ON ticket_checks(match_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_notifications_match ON notifications_sent(match_id, sent_at);
"""


class StateDB:
    """SQLite-backed state manager."""

    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ── Watches ──────────────────────────────────────────────────────────

    def add_watch(self, match_id: str, notify_email: bool = True, notify_desktop: bool = True) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO watches (match_id, added_at, notify_email, notify_desktop) "
            "VALUES (?, ?, ?, ?)",
            (match_id, datetime.now().isoformat(), int(notify_email), int(notify_desktop)),
        )
        self.conn.commit()

    def remove_watch(self, match_id: str) -> bool:
        cursor = self.conn.execute("DELETE FROM watches WHERE match_id = ?", (match_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_watches(self) -> list[UserWatch]:
        rows = self.conn.execute("SELECT * FROM watches").fetchall()
        return [
            UserWatch(
                match_id=r["match_id"],
                added_at=datetime.fromisoformat(r["added_at"]),
                last_notified=datetime.fromisoformat(r["last_notified"]) if r["last_notified"] else None,
                notify_email=bool(r["notify_email"]),
                notify_desktop=bool(r["notify_desktop"]),
            )
            for r in rows
        ]

    def is_watched(self, match_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM watches WHERE match_id = ?", (match_id,)).fetchone()
        return row is not None

    def update_last_notified(self, match_id: str) -> None:
        self.conn.execute(
            "UPDATE watches SET last_notified = ? WHERE match_id = ?",
            (datetime.now().isoformat(), match_id),
        )
        self.conn.commit()

    # ── Ticket Checks ────────────────────────────────────────────────────

    def save_ticket_check(self, status: TicketStatus) -> None:
        self.conn.execute(
            "INSERT INTO ticket_checks (match_id, available, categories, price_range, checked_at, ticket_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                status.match_id,
                int(status.available),
                json.dumps(status.categories),
                status.price_range,
                status.checked_at.isoformat(),
                status.ticket_url,
            ),
        )
        self.conn.commit()

    def get_last_ticket_status(self, match_id: str) -> TicketStatus | None:
        row = self.conn.execute(
            "SELECT * FROM ticket_checks WHERE match_id = ? ORDER BY checked_at DESC LIMIT 1",
            (match_id,),
        ).fetchone()
        if row is None:
            return None
        return TicketStatus(
            match_id=row["match_id"],
            available=bool(row["available"]),
            categories=json.loads(row["categories"]),
            price_range=row["price_range"],
            checked_at=datetime.fromisoformat(row["checked_at"]),
            ticket_url=row["ticket_url"],
        )

    # ── Notifications ────────────────────────────────────────────────────

    def record_notification(self, match_id: str, channel: str) -> None:
        self.conn.execute(
            "INSERT INTO notifications_sent (match_id, channel, sent_at) VALUES (?, ?, ?)",
            (match_id, channel, datetime.now().isoformat()),
        )
        self.conn.commit()

    def was_notified_recently(self, match_id: str, channel: str, within_minutes: int = 60) -> bool:
        """Check if a notification was already sent for this match within the given window."""
        row = self.conn.execute(
            "SELECT sent_at FROM notifications_sent "
            "WHERE match_id = ? AND channel = ? ORDER BY sent_at DESC LIMIT 1",
            (match_id, channel),
        ).fetchone()
        if row is None:
            return False
        last_sent = datetime.fromisoformat(row["sent_at"])
        elapsed = (datetime.now() - last_sent).total_seconds() / 60
        return elapsed < within_minutes
