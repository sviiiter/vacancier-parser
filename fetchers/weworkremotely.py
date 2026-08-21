import logging
from datetime import datetime, timezone

import feedparser

from models.message import Message

log = logging.getLogger(__name__)

_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
]


def fetch_weworkremotely_vacancies() -> list[Message]:
    messages: list[Message] = []
    for feed_url in _FEEDS:
        try:
            messages.extend(_parse_feed(feed_url))
        except Exception:
            log.exception("WeWorkRemotely: failed to parse %s", feed_url)
    return messages


def _parse_feed(feed_url: str) -> list[Message]:
    feed = feedparser.parse(feed_url)
    messages: list[Message] = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link:
            continue

        pub = entry.get("published_parsed")
        created = (
            datetime(*pub[:6], tzinfo=timezone.utc)
            if pub
            else datetime.now(timezone.utc)
        )

        title = entry.get("title", "")
        summary = entry.get("summary", "")
        desc = f"{title}\n{summary}".strip()

        messages.append(
            Message(
                description=desc,
                tg_channel_link="https://weworkremotely.com",
                tg_message_link=link,
                created_date=created,
                source="weworkremotely",
            )
        )

    log.info("WeWorkRemotely: fetched %d entries from %s", len(messages), feed_url)
    return messages
