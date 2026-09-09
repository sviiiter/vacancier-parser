import logging

import psycopg2.extensions
import redis

log = logging.getLogger(__name__)

MAX_MESSAGES_PER_SUBSCRIBER = 10


class CachePublisher:
    """Publish subscriber-relevant messages to Redis cache."""

    def __init__(self, conn: psycopg2.extensions.connection, redis_client: redis.Redis) -> None:
        self._conn = conn
        self._redis = redis_client

    def publish_for_subscribers(self) -> None:
        """
        For each subscriber, publish messages matching their filters to Redis.
        Respects trial message limits and publishes max 10 messages per subscriber.
        Updates message_sent_last_date to the created_date of the last message sent.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.chat_id, s.message_sent_last_date, s.plan, s.messages_received,
                       array_agg(DISTINCT sf.filter_id) AS filter_ids
                FROM subscriber_filters sf
                JOIN subscribers s ON s.id = sf.subscriber_id
                WHERE s.active = 1
                GROUP BY s.id, s.chat_id, s.message_sent_last_date, s.plan, s.messages_received
                """
            )
            subscribers = cur.fetchall()

        # Get bot settings for trial limits
        settings = self._get_settings()

        for sub_row in subscribers:
            sub_id = sub_row["id"]
            chat_id = sub_row["chat_id"]
            filter_ids = sub_row["filter_ids"] or []
            last_date = sub_row["message_sent_last_date"]
            plan = sub_row["plan"]
            messages_received = sub_row["messages_received"] or 0

            if not filter_ids:
                continue

            # Calculate message limit based on plan
            if plan == "free":
                if settings["trial_type"] == "messages":
                    messages_limit = settings["trial_message_limit"]
                else:
                    messages_limit = None  # Trial is time-based, no message limit
            else:
                messages_limit = None  # Paid plans have no message limit

            # Check if subscriber has reached message limit
            if messages_limit and messages_received >= messages_limit:
                log.debug("Subscriber %s reached message limit (%d/%d)", chat_id, messages_received, messages_limit)
                continue

            # Calculate remaining messages allowed
            remaining_limit = messages_limit - messages_received if messages_limit else None
            fetch_limit = min(remaining_limit, MAX_MESSAGES_PER_SUBSCRIBER) if remaining_limit else MAX_MESSAGES_PER_SUBSCRIBER

            # Get messages matching subscriber's filters, newer than last_date
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT m.id, m.created_date
                    FROM messages m
                    JOIN message_filters mf ON mf.message_id = m.id
                    WHERE mf.filter_id = ANY(%s)
                      AND (%s::timestamptz IS NULL OR m.created_date > %s)
                    ORDER BY m.created_date ASC
                    LIMIT %s
                    """,
                    (filter_ids, last_date, last_date, fetch_limit),
                )
                rows = cur.fetchall()

            if not rows:
                continue

            message_ids = [row['id'] for row in rows]
            last_message_date = rows[-1]['created_date']

            # Publish to Redis (max 10 messages per subscriber)
            self._redis.sadd(f"pending:{chat_id}", *message_ids)
            self._redis.sadd("pending:index", chat_id)

            # Update subscriber's message_sent_last_date and messages_received
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE subscribers
                    SET message_sent_last_date = %s,
                        messages_received = messages_received + %s
                    WHERE id = %s
                    """,
                    (last_message_date, len(message_ids), sub_id),
                )
            self._conn.commit()

            log.info("Published %d message(s) for chat_id=%s (limit: %s, received: %d)",
                     len(message_ids), chat_id, messages_limit or "unlimited",
                     messages_received + len(message_ids))

    def _get_settings(self) -> dict:
        """Get bot settings from database."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT trial_type, trial_message_limit FROM bot_settings WHERE id = 1"
            )
            row = cur.fetchone()

        if row:
            return {
                "trial_type": row["trial_type"],
                "trial_message_limit": row["trial_message_limit"],
            }
        return {
            "trial_type": "messages",
            "trial_message_limit": 10,
        }
