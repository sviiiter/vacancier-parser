# Vacancier — Telegram Channel Parser

Fetches messages from a list of Telegram channels, filters by keywords (`PHP`, `backend`, `senior`),
deduplicates by message link, and persists matching vacancies to a local SQLite database.
Runs nightly at 02:00 UTC inside a Docker container via `supercronic`.

---

## File Structure

```
vacancier/
│
├── config.py                   # Central config: channel list, keywords, DB path, Telegram credentials
│
├── models/
│   └── message.py              # Message dataclass — shared data contract across all layers
│
├── database/
│   ├── connection.py           # SQLite connection factory + schema initialisation (CREATE TABLE IF NOT EXISTS)
│   └── repository.py           # MessageRepository — get_last_created_date, get_existing_links, save
│
├── processor/                  # Pure logic — no I/O, no database; fully unit-testable
│   ├── interfaces.py           # MessageFilterProtocol, DuplicateCheckerProtocol (typing.Protocol)
│   ├── keyword_filter.py       # KeywordFilter — case-insensitive keyword match against description
│   ├── duplicate_checker.py    # DuplicateChecker — tracks seen tg_message_link values in a set
│   └── message_processor.py   # MessageProcessor — orchestrates filter + duplicate check (DI via constructor)
│
├── telegram/
│   └── client.py               # TelegramChannelFetcher — async context manager wrapping Telethon; fetches
│                               #   messages newer than the last stored date, newest-first, breaks on cutoff
│
├── parser.py                   # Entry point: wires DB → fetcher → processor → repository; run by cron
│
├── generate_session.py         # One-time helper: interactive Telegram login → prints session string for .env
│
├── tests/                      # Pure unit tests — zero database, zero Telegram, zero I/O
│   ├── test_keyword_filter.py  # Tests: exact/lower/mixed case, no match, empty string
│   ├── test_duplicate_checker.py  # Tests: first occurrence, repeat, pre-seeded set, different links
│   └── test_message_processor.py  # Tests: filter pass/fail, duplicate, mixed batch, empty input
│                               #   Uses inline stub classes (no mocking library needed)
│
├── Dockerfile                  # python:3.12-slim + supercronic; ENTRYPOINT runs crontab
├── crontab                     # supercronic schedule: runs parser.py at 02:00 UTC every night
├── docker-compose.yml          # Mounts ./data volume for SQLite persistence; reads .env
│
├── requirements.txt            # telethon, python-dotenv
├── .env.example                # Template for required environment variables
└── .gitignore                  # Excludes .env, data/, *.session, __pycache__
```

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    description     TEXT NOT NULL,
    tg_channel_link TEXT NOT NULL,
    tg_message_link TEXT NOT NULL UNIQUE,  -- duplicate guard at DB level
    created_date    TEXT NOT NULL           -- ISO 8601 UTC string
);
```

---

## Setup

### 1. Telegram API credentials

1. Go to <https://my.telegram.org/apps> and create an application.
2. Copy **App api_id** and **App api_hash**.

### 2. Generate a session string (one-time, run locally)

```bash
cp .env.example .env
# fill in TELEGRAM_API_ID and TELEGRAM_API_HASH in .env

pip install -r requirements.txt
python generate_session.py
```

Enter your phone number and the SMS verification code. The script prints a long string — paste it into `.env` as `TELEGRAM_SESSION_STRING`.

### 3. Configure channels

Edit `config.py` and replace the example channel names in `TELEGRAM_CHANNELS` with the actual public channel usernames you want to monitor (without `@`).

---

## Running locally

```bash
python parser.py
```

Logs go to stdout. The database is created at the path set by `DB_PATH` (default: `data/vacancier.db`).

---

## Running tests

```bash
python -m unittest discover tests/
```

No database or Telegram connection is required — all tests are pure unit tests.

---

## Docker

### Build and start

```bash
docker compose up -d
```

The container runs `parser.py` every night at **02:00 UTC**. Logs are visible via:

```bash
docker compose logs -f
```

### Data persistence

`./data/` on the host is mounted to `/app/data/` inside the container, so `vacancier.db` survives restarts and image rebuilds.

### Changing the schedule

Edit `crontab` (standard cron syntax) and rebuild:

```bash
docker compose up -d --build
```

---

## Authentication note

The parser authenticates as a **regular Telegram user account** via Telethon (MTProto). This allows reading message history from any public channel without being an admin. The session is stored as a string in the `TELEGRAM_SESSION_STRING` environment variable — no interactive login is needed inside the container after the initial `generate_session.py` run.
