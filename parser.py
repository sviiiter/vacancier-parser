import asyncio
import logging

from config import (
    DB_PATH,
    KEYWORDS,
    TELEGRAM_API_HASH,
    TELEGRAM_API_ID,
    TELEGRAM_CHANNELS,
    TELEGRAM_SESSION_STRING,
)
from database.connection import get_connection, init_schema
from database.repository import MessageRepository
from processor.duplicate_checker import DuplicateChecker
from processor.keyword_filter import KeywordFilter
from processor.message_processor import MessageProcessor
from telegram.client import TelegramChannelFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    conn = get_connection(DB_PATH)
    init_schema(conn)
    repo = MessageRepository(conn)

    last_date = repo.get_last_created_date()
    existing_links = repo.get_existing_links()
    log.info("Last message date in DB: %s", last_date)
    log.info("Known links in DB: %d", len(existing_links))

    processor = MessageProcessor(
        filter=KeywordFilter(KEYWORDS),
        checker=DuplicateChecker(existing_links),
    )

    async with TelegramChannelFetcher(
        TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING
    ) as fetcher:
        for channel in TELEGRAM_CHANNELS:
            log.info("Processing channel: %s", channel)
            try:
                raw = await fetcher.fetch_new_messages(channel, last_date)
                log.info("  Fetched %d new messages", len(raw))

                passing = processor.process(raw)
                log.info("  %d messages passed filter", len(passing))

                for msg in passing:
                    repo.save(msg)
                    log.info("  Saved: %s", msg.tg_message_link)

            except Exception:
                log.exception("Failed to process channel %s", channel)

    conn.close()
    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
