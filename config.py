import json
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID: int = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH: str = os.environ["TELEGRAM_API_HASH"]
TELEGRAM_SESSION_STRING: str = os.environ["TELEGRAM_SESSION_STRING"]

TELEGRAM_CHANNELS: list[str] = [
    "recrytingIT",
    "jc_it",
    "serbia_jobs",
    "Remoteit",
    "php_jobs",
    "fordev",
    "devs_it",
    "jobforphp",
    "jobGeeks",
    "it_jobs_armenia",
]

FILTER_RULES: dict = json.loads(os.environ.get("FILTER_RULES", json.dumps({
    "required": ["php"],
    "any": ["developer", "engineer", "backend"],
    "exclude": ["wordpress"]
})))

# HeadHunter
HH_KEYWORDS: list[str] = json.loads(
    os.environ.get("HH_KEYWORDS", '["PHP Senior", "Python Senior", "backend senior"]')
)
HH_AREA: int = int(os.environ.get("HH_AREA", "0"))  # 0 = all regions

# RemoteOK — empty list means no tag filter (return all jobs)
REMOTEOK_TAGS: list[str] = json.loads(os.environ.get("REMOTEOK_TAGS", "[]"))

# LinkedIn — empty list disables the LinkedIn fetcher
LINKEDIN_KEYWORDS: list[str] = json.loads(os.environ.get("LINKEDIN_KEYWORDS", "[]"))

# Generic RSS feeds (GitHub Jobs-like boards)
RSS_FEEDS: list[str] = json.loads(
    os.environ.get(
        "RSS_FEEDS",
        json.dumps([
            "https://remotive.com/remote-jobs/software-dev/feed/",
            "https://remote.co/remote-jobs/developer/feed/",
            "https://www.indeed.com/rss?q=PHP+senior+remote&sort=date",
        ]),
    )
)

# RabbitMQ
RABBITMQ_URL: str = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
