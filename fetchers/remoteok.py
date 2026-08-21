import logging
from datetime import datetime, timezone

import requests

from models.message import Message

log = logging.getLogger(__name__)

_API_URL = "https://remoteok.com/api"
_HEADERS = {"User-Agent": "vacancier-parser/1.0 (resvit@gmail.com)"}


def fetch_remoteok_vacancies(tags: list[str] | None = None) -> list[Message]:
    try:
        resp = requests.get(_API_URL, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        log.exception("RemoteOK: request failed")
        return []

    jobs = resp.json()
    # First element is API metadata, not a job
    if jobs and isinstance(jobs[0], dict) and "legal" in jobs[0]:
        jobs = jobs[1:]

    filter_tags = {t.lower() for t in (tags or [])}
    messages: list[Message] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue

        if filter_tags:
            job_tags = {t.lower() for t in job.get("tags", [])}
            if not filter_tags.intersection(job_tags):
                continue

        url = job.get("url", "")
        if not url:
            continue

        date_raw = job.get("date", "")
        try:
            created = datetime.fromisoformat(date_raw)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            created = datetime.now(timezone.utc)

        position = job.get("position") or ""
        company = job.get("company") or ""
        description = job.get("description") or ""
        desc = f"{position} at {company}\n{description}".strip()

        messages.append(
            Message(
                description=desc,
                tg_channel_link="https://remoteok.com",
                tg_message_link=url,
                created_date=created,
                source="remoteok",
            )
        )

    log.info("RemoteOK: fetched %d vacancies", len(messages))
    return messages
