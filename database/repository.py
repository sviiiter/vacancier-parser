import hashlib
import json
from datetime import datetime

import psycopg2.extensions

from models.message import Message


class MessageRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def get_last_created_date(self) -> datetime | None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT MAX(created_date) AS last_date FROM messages")
            row = cur.fetchone()
        if row["last_date"] is None:
            return None
        return row["last_date"]  # psycopg2 returns a timezone-aware datetime for TIMESTAMPTZ

    def get_existing_links(self) -> set[str]:
        with self._conn.cursor() as cur:
            cur.execute("SELECT tg_message_link FROM messages")
            return {row["tg_message_link"] for row in cur.fetchall()}

    def exists(self, tg_message_link: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM messages WHERE tg_message_link = %s",
                (tg_message_link,),
            )
            return cur.fetchone() is not None

    def exists_by_fingerprint(self, fingerprint: str) -> bool:
        if not fingerprint:
            return False
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM messages WHERE fingerprint = %s",
                (fingerprint,),
            )
            return cur.fetchone() is not None

    def save(self, message: Message) -> int | None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                    (description, tg_channel_link, tg_message_link, created_date, source, queue_sent, read, fingerprint, matched_keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tg_message_link) DO NOTHING
                RETURNING id
                """,
                (
                    message.description,
                    message.tg_channel_link,
                    message.tg_message_link,
                    message.created_date,
                    message.source,
                    message.queue_sent,
                    message.read,
                    message.fingerprint,
                    json.dumps(message.matched_keywords),
                ),
            )
            row = cur.fetchone()
            if row is not None:
                self._conn.commit()
                return row["id"]
            cur.execute(
                "SELECT id FROM messages WHERE tg_message_link = %s",
                (message.tg_message_link,),
            )
            row = cur.fetchone()
        return row["id"] if row else None
