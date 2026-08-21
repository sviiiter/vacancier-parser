import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from config import (
    HH_AREA,
    HH_KEYWORDS,
    LINKEDIN_KEYWORDS,
    RABBITMQ_URL,
    REMOTEOK_TAGS,
    RSS_FEEDS,
    TELEGRAM_API_HASH,
    TELEGRAM_API_ID,
    TELEGRAM_CHANNELS,
    TELEGRAM_SESSION_STRING,
)
from database.connection import get_connection, init_schema
from database.repository import MessageRepository
from fetchers.hh import fetch_hh_vacancies
from fetchers.linkedin import fetch_linkedin_vacancies
from fetchers.remoteok import fetch_remoteok_vacancies
from fetchers.rss import fetch_rss_vacancies
from fetchers.weworkremotely import fetch_weworkremotely_vacancies
from models.message import Message
from rabbitmq_queue.publisher import JobPublisher
from telegram.client import TelegramChannelFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    conn = get_connection(database_url)
    init_schema(conn)
    repo = MessageRepository(conn)

    last_date = repo.get_last_created_date()
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
    since = max(last_date, two_days_ago) if last_date is not None else two_days_ago
    existing_links = repo.get_existing_links()
    log.info("Fetching messages since: %s", since)
    log.info("Known links in DB: %d", len(existing_links))

    publisher = JobPublisher(RABBITMQ_URL)

    total_published = 0

    # --- Sync HTTP fetchers ---
    log.info("Fetching from HH...")
    for msg in fetch_hh_vacancies(HH_KEYWORDS, HH_AREA):
        if msg.tg_message_link not in existing_links:
            publisher.publish(msg)
            total_published += 1

    log.info("Fetching from RemoteOK...")
    for msg in fetch_remoteok_vacancies(REMOTEOK_TAGS):
        if msg.tg_message_link not in existing_links:
            publisher.publish(msg)
            total_published += 1

    log.info("Fetching from WeWorkRemotely...")
    for msg in fetch_weworkremotely_vacancies():
        if msg.tg_message_link not in existing_links:
            publisher.publish(msg)
            total_published += 1

    log.info("Fetching from RSS feeds...")
    for msg in fetch_rss_vacancies(RSS_FEEDS):
        if msg.tg_message_link not in existing_links:
            publisher.publish(msg)
            total_published += 1

    if LINKEDIN_KEYWORDS:
        log.info("Fetching from LinkedIn...")
        for msg in fetch_linkedin_vacancies(LINKEDIN_KEYWORDS):
            if msg.tg_message_link not in existing_links:
                publisher.publish(msg)
                total_published += 1

    # --- Async Telegram fetcher ---
    async with TelegramChannelFetcher(
        TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING
    ) as fetcher:
        for channel in TELEGRAM_CHANNELS:
            log.info("Processing Telegram channel: %s", channel)
            try:
                raw = await fetcher.fetch_new_messages(channel, since)
                log.info("  Fetched %d new messages", len(raw))
                for msg in raw:
                    if msg.tg_message_link not in existing_links:
                        publisher.publish(msg)
                        total_published += 1
            except Exception:
                log.exception("Failed to process channel %s", channel)

    log.info("Published %d messages to queue", total_published)
    publisher.close()
    conn.close()
    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
