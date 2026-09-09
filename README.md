# Vacancier — Telegram Channel Parser v2

A three-stage job posting pipeline:

1. **Parser** (`parser.py`): Fetches messages from Telegram channels, deduplicates by link + content fingerprint, saves raw messages to database
2. **Matcher** (`matcher.py`): Matches saved messages against subscriber filters (keyword-based or OpenAI-based), tags message-filter relationships
3. **Cache Publisher** (`cache/publisher.py`): Stages matched messages to Redis for subscribers, respecting trial quota *read-only* (no quota updates)

The Telegram bot (`vacancier-tg-bot`) drains the Redis queue and sends messages to subscribers, updating quota counters only after confirmed delivery.

---

## File Structure

```
vacancier/
│
├── config.py                   # Central config: DB, Redis, Telegram credentials
│
├── models/
│   └── message.py              # Message dataclass — shared data contract
│
├── database/
│   ├── connection.py           # PostgreSQL connection + schema init
│   ├── filter_repository.py    # FilterRepository — load filters, save message-filter tags
│   └── message_repository.py   # MessageRepository — save, fetch, check duplicates
│
├── parser.py                   # Stage 1: Fetch new messages from Telegram channels
│
├── worker.py                   # Stage 1b: Deduplicate (by link + fingerprint), strip HTML, save to DB
│
├── processor/                  # Stage 2: Match messages against subscriber filters
│   ├── matcher_protocol.py     # MatchProcessor — interface for matching strategies
│   ├── keyword_matcher.py      # KeywordMatcher — rule-based filtering (required/any/exclude)
│   ├── openai_matcher.py       # OpenAIMatcher — AI-based filtering from uploaded files
│   └── duplicate_checker.py    # DuplicateChecker — SHA256 fingerprinting for content dedup
│
├── cache/
│   └── publisher.py            # Stage 3: Stage matched messages to Redis (quota read-only)
│                               #   Bot updates quota counters after actual delivery
│
├── matcher.py                  # Orchestrates: load filters → match messages → publish to Redis
│
├── database_fill.py            # Helper: populate filters table from JSON files
│
├── tests/                      # Unit tests — zero live DB/API/Telegram
│   ├── test_keyword_matcher.py # Tests: required/any/exclude rules, combined
│   └── test_*.py               # More comprehensive test coverage
│
├── Dockerfile                  # python:3.12 + matcher job runner
├── docker-compose.yml          # Services: postgres, redis, parser, matcher containers
│
├── requirements.txt            # psycopg2-binary, redis, requests
├── .env.example                # Template for DATABASE_URL, REDIS_URL, etc.
└── .gitignore                  # Excludes .env, __pycache__, .pytest_cache
```

---

## Database Schema

**messages** — Job postings from Telegram channels
```sql
CREATE TABLE IF NOT EXISTS messages (
    id                  SERIAL PRIMARY KEY,
    description         TEXT NOT NULL,
    tg_channel_link     TEXT NOT NULL,
    tg_message_link     TEXT NOT NULL UNIQUE,  -- dedup by link
    fingerprint         TEXT,                  -- SHA256 of normalized text, dedup by content
    created_date        TIMESTAMP NOT NULL,
    source              TEXT
);
```

**filters** — Subscriber-defined filter rules
```sql
CREATE TABLE IF NOT EXISTS filters (
    id                  SERIAL PRIMARY KEY,
    subscriber_id       INT NOT NULL,
    name                VARCHAR(255),
    type                VARCHAR(10),           -- 'json' or 'file'
    extra               TEXT,                  -- filter rules (JSON or file path)
    created_at          TIMESTAMP DEFAULT NOW()
);
```

**message_filters** — Relationship between messages and matching filters
```sql
CREATE TABLE IF NOT EXISTS message_filters (
    id                  SERIAL PRIMARY KEY,
    message_id          INT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filter_id           INT NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE (message_id, filter_id)
);
```

**bot_settings** — Trial configuration for the bot
```sql
CREATE TABLE IF NOT EXISTS bot_settings (
    id                  INT PRIMARY KEY,
    trial_type          VARCHAR(50) DEFAULT 'messages',  -- 'messages' or 'days'
    trial_message_limit INT DEFAULT 10,
    trial_days          INT DEFAULT 2
);
```

---

## Setup

### Prerequisites

- PostgreSQL (or MySQL/SQLite)
- Redis
- Python 3.11+
- Telegram account (for fetching channel messages)

### Configuration

```bash
cp .env.example .env
```

Fill in:
- `DATABASE_URL` — PostgreSQL/MySQL/SQLite connection string
- `REDIS_URL` — Redis connection URL (e.g., `redis://localhost:6379`)
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` — from https://my.telegram.org/apps
- `TELEGRAM_SESSION_STRING` — generate via `python generate_session.py` (one-time)

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running Locally

**Stage 1: Fetch and save messages**
```bash
python parser.py
```
Fetches new messages from configured Telegram channels, deduplicates, strips HTML, saves to DB.

**Stage 2: Match messages against filters**
```bash
python matcher.py
```
Loads all filters, matches untagged messages, stages matched messages to Redis cache.

**Stage 3: Bot drains cache**
Run the bot repo (`vacancier-tg-bot/bot/main.py`) to deliver staged messages to subscribers.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests are isolated (no real DB/Redis/Telegram required).

---

## Docker Compose

```bash
docker compose up -d
```

Starts:
- PostgreSQL database
- Redis cache
- Parser (cron: daily fetch)
- Matcher (cron: continuous message matching)

Logs:
```bash
docker compose logs -f matcher
docker compose logs -f parser
```

---

## Data Flow

```
1. parser.py 
   ↓ (fetch, deduplicate, strip HTML)
   
2. database: messages table
   ↓
   
3. matcher.py
   ↓ (match against subscriber filters)
   
4. database: message_filters table
   ↓
   
5. cache/publisher.py
   ↓ (stage to Redis, quota read-only)
   
6. Redis: pending:{chat_id} sets
   ↓
   
7. Bot (vacancier-tg-bot/bot/main.py)
   ↓ (drain, deliver, update quota counters)
   
8. Subscribers receive messages in Telegram
```

**Key point**: The matcher only stages messages to Redis. The bot is responsible for respecting trial quotas and updating `messages_received` counters after confirmed delivery.
