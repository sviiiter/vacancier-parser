import sqlite3
from datetime import datetime

from models.message import Message


class MessageRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_last_created_date(self) -> datetime | None:
        row = self._conn.execute(
            "SELECT MAX(created_date) AS last_date FROM messages"
        ).fetchone()
        if row["last_date"] is None:
            return None
        return datetime.fromisoformat(row["last_date"])

    def get_existing_links(self) -> set[str]:
        rows = self._conn.execute("SELECT tg_message_link FROM messages").fetchall()
        return {row["tg_message_link"] for row in rows}

    def exists(self, tg_message_link: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM messages WHERE tg_message_link = ?",
            (tg_message_link,),
        ).fetchone()
        return row is not None

    def save(self, message: Message) -> None:
        try:
            self._conn.execute(
                """
                INSERT INTO messages (description, tg_channel_link, tg_message_link, created_date, queue_sent, read)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.description,
                    message.tg_channel_link,
                    message.tg_message_link,
                    message.created_date.isoformat(),
                    int(message.queue_sent),
                    int(message.read),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass  # UNIQUE constraint: silently skip exact duplicates
