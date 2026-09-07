import logging

import psycopg2.extensions
import redis

log = logging.getLogger(__name__)


class CachePublisher:
    """Publish subscriber-relevant messages to Redis cache."""

    def __init__(self, conn: psycopg2.extensions.connection, redis_client: redis.Redis) -> None:
        self._conn = conn
        self._redis = redis_client

    def publish_for_subscribers(self) -> None:
        """
        For each subscriber, publish messages matching their filters to Redis.
        Only publishes messages newer than subscriber's message_sent_last_date.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.chat_id, s.message_sent_last_date,
                       array_agg(DISTINCT sf.filter_id) AS filter_ids
                FROM subscriber_filters sf
                JOIN subscribers s ON s.id = sf.subscriber_id
                WHERE s.active = 1
                GROUP BY s.id, s.chat_id, s.message_sent_last_date
                """
            )
            subscribers = cur.fetchall()

        for sub_row in subscribers:
            chat_id = sub_row["chat_id"]
            filter_ids = sub_row["filter_ids"] or []
            last_date = sub_row["message_sent_last_date"]

            if not filter_ids:
                continue

            # Get messages matching subscriber's filters, newer than last_date
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT m.id
                    FROM messages m
                    JOIN message_filters mf ON mf.message_id = m.id
                    WHERE mf.filter_id = ANY(%s)
                      AND (%s::timestamptz IS NULL OR m.created_date > %s)
                    ORDER BY m.created_date ASC
                    """,
                    (filter_ids, last_date, last_date),
                )
                message_ids = [row[0] for row in cur.fetchall()]

            # Publish to Redis
            if message_ids:
                self._redis.sadd(f"pending:{chat_id}", *message_ids)
                self._redis.sadd("pending:index", chat_id)
                log.info("Published %d message(s) for chat_id=%s", len(message_ids), chat_id)
