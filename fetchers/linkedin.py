import logging
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from models.message import Message

log = logging.getLogger(__name__)

_GUEST_API = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_linkedin_vacancies(keywords: list[str]) -> list[Message]:
    if not keywords:
        return []
    messages: list[Message] = []
    for keyword in keywords:
        try:
            messages.extend(_fetch_keyword(keyword))
        except Exception:
            log.exception("LinkedIn: failed to fetch keyword %r", keyword)
    return messages


def _fetch_keyword(keyword: str) -> list[Message]:
    params = {"keywords": keyword, "start": 0, "count": 25}
    resp = requests.get(_GUEST_API, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.find_all("div", attrs={"data-entity-urn": re.compile(r"jobPosting")})

    messages: list[Message] = []
    for card in cards:
        urn = card.get("data-entity-urn", "")
        match = re.search(r":(\d+)$", urn)
        if not match:
            continue
        job_id = match.group(1)
        vacancy_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

        title_el = card.find(class_="base-search-card__title")
        company_el = card.find(class_="base-search-card__subtitle")
        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        desc = f"{title} at {company}".strip(" at").strip()

        time_el = card.find("time")
        created: datetime
        if time_el and time_el.get("datetime"):
            try:
                created = datetime.fromisoformat(time_el["datetime"])
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
            except ValueError:
                created = datetime.now(timezone.utc)
        else:
            created = datetime.now(timezone.utc)

        messages.append(
            Message(
                description=desc,
                tg_channel_link="https://www.linkedin.com/jobs",
                tg_message_link=vacancy_url,
                created_date=created,
                source="linkedin",
            )
        )

    log.info("LinkedIn: fetched %d vacancies for %r", len(messages), keyword)
    return messages
