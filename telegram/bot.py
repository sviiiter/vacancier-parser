import json
import logging
from typing import Optional

import psycopg2.extensions
import redis
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest

log = logging.getLogger(__name__)


class VacancierBot:
    """Telegram bot for job vacancy subscribers."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_string: str,
        db_conn: psycopg2.extensions.connection,
        redis_client: redis.Redis,
    ) -> None:
        self._client = TelegramClient(
            StringSession(session_string), api_id, api_hash
        )
        self._db = db_conn
        self._redis = redis_client

    async def start(self) -> None:
        """Start the bot and register handlers."""
        await self._client.connect()
        await self._client.start()

        self._client.add_event_handler(
            self._handle_start, events.NewMessage(pattern="/start")
        )
        self._client.add_event_handler(
            self._handle_filters, events.NewMessage(pattern="/filters")
        )
        self._client.add_event_handler(
            self._handle_add_filter, events.NewMessage(pattern="/add_filter")
        )
        self._client.add_event_handler(
            self._handle_updates, events.NewMessage(pattern="/updates")
        )

        await self._client.run_until_disconnected()

    async def stop(self) -> None:
        """Stop the bot."""
        await self._client.disconnect()

    def _is_subscribed(self, chat_id: int) -> bool:
        """Check if user is subscribed."""
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT active FROM subscribers WHERE chat_id = %s",
                (chat_id,),
            )
            result = cur.fetchone()
            return result is not None and result["active"] == 1

    def _get_subscriber_id(self, chat_id: int) -> Optional[int]:
        """Get subscriber ID from chat_id."""
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT id FROM subscribers WHERE chat_id = %s",
                (chat_id,),
            )
            result = cur.fetchone()
            return result["id"] if result else None

    async def _handle_start(self, event) -> None:
        """Handle /start command."""
        chat_id = event.chat_id

        if not self._is_subscribed(chat_id):
            await event.respond(
                "You need to be subscribed to use this bot.\n\n"
                "Available commands:\n"
                "/filters - List your filters\n"
                "/add_filter - Add a new filter\n"
                "/updates - Get latest job updates"
            )
            return

        await event.respond(
            "Welcome to Vacancier! 🎯\n\n"
            "Available commands:\n"
            "/filters - List your filters\n"
            "/add_filter - Add a new filter\n"
            "/updates - Get latest job updates"
        )

    async def _handle_filters(self, event) -> None:
        """Handle /filters command - list user filters."""
        chat_id = event.chat_id

        if not self._is_subscribed(chat_id):
            await event.respond("You need to be subscribed to use this bot.")
            return

        subscriber_id = self._get_subscriber_id(chat_id)
        if not subscriber_id:
            await event.respond("Error: Subscriber not found.")
            return

        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT f.id, f.name, f.type, f.extra
                FROM filters f
                JOIN subscriber_filters sf ON f.id = sf.filter_id
                WHERE sf.subscriber_id = %s
                """,
                (subscriber_id,),
            )
            filters = cur.fetchall()

        if not filters:
            await event.respond("You have no filters configured.")
            return

        response = "Your filters:\n\n"
        for f in filters:
            filter_type = f["type"]
            if filter_type == "json":
                keywords = json.loads(f["extra"])
                response += f"#{f['id']} {f['name']}: {', '.join(keywords)}\n"
            else:
                response += f"#{f['id']} {f['name']} (OpenAI)\n"

        await event.respond(response)

    async def _handle_add_filter(self, event) -> None:
        """Handle /add_filter command - add a new filter."""
        chat_id = event.chat_id

        if not self._is_subscribed(chat_id):
            await event.respond("You need to be subscribed to use this bot.")
            return

        await event.respond(
            "Filter creation coming soon!\n"
            "Currently, please contact support to add filters."
        )

    async def _handle_updates(self, event) -> None:
        """Handle /updates command - get pending messages from Redis."""
        chat_id = event.chat_id

        if not self._is_subscribed(chat_id):
            await event.respond("You need to be subscribed to use this bot.")
            return

        # Get pending message IDs from Redis
        key = f"pending:{chat_id}"
        message_ids = self._redis.smembers(key)

        if not message_ids:
            await event.respond("No new updates available.")
            return

        # Fetch messages from database
        message_ids_list = [int(m) for m in message_ids]

        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT id, description, tg_message_link, source, created_date
                FROM messages
                WHERE id = ANY(%s)
                ORDER BY created_date DESC
                LIMIT 10
                """,
                (message_ids_list,),
            )
            messages = cur.fetchall()

        if not messages:
            await event.respond("No updates available.")
            return

        response = f"📋 Latest job updates ({len(messages)} new):\n\n"
        for msg in messages:
            desc = msg["description"][:100].strip()
            response += f"🔗 {msg['tg_message_link']}\n{desc}...\n\n"

        await event.respond(response)

        # Clear pending messages for this subscriber
        self._redis.delete(key)

        # Update last sent date
        subscriber_id = self._get_subscriber_id(chat_id)
        if subscriber_id:
            with self._db.cursor() as cur:
                cur.execute(
                    "UPDATE subscribers SET message_sent_last_date = now() WHERE id = %s",
                    (subscriber_id,),
                )
            self._db.commit()
