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
    "@it_jobs_armenia",
]

KEYWORDS: list[str] = ["PHP", "backend", "senior"]

DB_PATH: str = os.getenv("DB_PATH", "data/vacancier.db")
