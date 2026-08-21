import logging
from datetime import datetime, timezone

import requests

from models.message import Message

log = logging.getLogger(__name__)

_BASE_URL = "https://api.hh.ru/vacancies"
_HEADERS = {"User-Agent": "vacancier-parser/1.0 (resvit@gmail.com)"}


def fetch_hh_vacancies(keywords: list[str], area: int = 0) -> list[Message]:
    messages: list[Message] = []
    for keyword in keywords:
        try:
            messages.extend(_fetch_keyword(keyword, area))
        except Exception:
            log.exception("HH: failed to fetch keyword %r", keyword)
    return messages


def _fetch_keyword(keyword: str, area: int) -> list[Message]:
    params: dict = {"text": keyword, "period": 1, "per_page": 50}
    if area:
        params["area"] = area

    resp = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    messages: list[Message] = []
    for item in data.get("items", []):
        snippet = item.get("snippet") or {}
        parts = [item["name"]]
        if snippet.get("requirement"):
            parts.append(snippet["requirement"])
        if snippet.get("responsibility"):
            parts.append(snippet["responsibility"])

        published_raw = item.get("published_at", "")
        try:
            created = datetime.fromisoformat(published_raw)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except ValueError:
            created = datetime.now(timezone.utc)

        messages.append(
            Message(
                description="\n".join(parts),
                tg_channel_link="https://hh.ru",
                tg_message_link=item["alternate_url"],
                created_date=created,
                source="hh",
            )
        )
    log.info("HH: fetched %d vacancies for %r", len(messages), keyword)
    return messages
