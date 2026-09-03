import logging
from datetime import datetime, timezone

import feedparser
import requests
import io

from models.message import Message

log = logging.getLogger(__name__)


def fetch_rss_vacancies(feed_urls: list[str]) -> list[Message]:
    messages: list[Message] = []
    for url in feed_urls:
        try:
            messages.extend(_parse_feed(url))
        except Exception:
            log.exception("RSS: failed to parse %s", url)
    return messages


def _parse_feed(feed_url: str) -> list[Message]:
    # Do request using requests library and timeout
    try:
        resp = requests.get(feed_url, timeout=20.0)
    except requests.ReadTimeout:
        log.warning("Timeout when reading RSS %s", feed_url)
        return

    # Put it to memory stream object universal feedparser
    content = io.BytesIO(resp.content)

    # Parse content
    feed = feedparser.parse(content)
    source_link = feed.feed.get("link", feed_url)

    messages: list[Message] = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link:
            continue

        pub = entry.get("published_parsed") or entry.get("updated_parsed")
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
                tg_channel_link=source_link,
                tg_message_link=link,
                created_date=created,
                source="rss",
            )
        )

    log.info("RSS: fetched %d entries from %s", len(messages), feed_url)
    return messages
