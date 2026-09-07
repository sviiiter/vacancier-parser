import asyncio
import logging
import os

import redis

from config import REDIS_URL, TELEGRAM_API_HASH, TELEGRAM_API_ID, TELEGRAM_SESSION_STRING
from database.connection import get_connection, init_schema
from telegram.bot import VacancierBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


async def run_bot() -> None:
    """Run the Telegram bot."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        log.error("DATABASE_URL not set")
        return

    db_conn = get_connection(database_url)
    init_schema(db_conn)
    redis_client = redis.from_url(REDIS_URL)

    bot = VacancierBot(
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH,
        TELEGRAM_SESSION_STRING,
        db_conn,
        redis_client,
    )

    try:
        log.info("Starting Telegram bot")
        await bot.start()
    except Exception as e:
        log.error("Bot error: %s", e)
    finally:
        db_conn.close()
        redis_client.close()


if __name__ == "__main__":
    asyncio.run(run_bot())
