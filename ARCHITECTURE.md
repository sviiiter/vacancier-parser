# vacancier-parser-v2: RabbitMQ-based Job Ingestion Pipeline

## Overview

`vacancier-parser-v2` refactors the original `vacancier-parser` to decouple fetching from processing via a RabbitMQ message queue. This enables independent scaling of producers (fetchers) and consumers (workers), graceful handling of slow sources (LinkedIn scraping, Telegram rate limits), and a clean separation of concerns.

## Architecture

```
Scheduler (supercronic, cron-driven)
   │
   ▼
Producers (6 fetchers)
   │  Fetch from: Telegram, HH.ru, RemoteOK, WeWorkRemotely, RSS, LinkedIn
   │  Each fetcher publishes to RabbitMQ immediately
   ▼
RabbitMQ Queue: "jobs.raw"
   │  Durable queue with DLX to "jobs.raw.dlq" for poison messages
   ▼
Worker (long-running consumer)
   ├── Deserialize Message from JSON
   ├── Run through KeywordFilter (required/any/exclude rules)
   ├── If rejected: ack and drop (no raw storage)
   ├── If passed:
   │   ├── Generate fingerprint (SHA256 of normalized description)
   │   ├── Check link UNIQUE constraint
   │   ├── Check fingerprint UNIQUE constraint
   │   └── Save to PostgreSQL with matched_keywords JSONB
   └── On error: nack without requeue → DLQ
```

## Key Changes from v1

### Producer (parser.py)
- **Before**: Collected all messages in memory, then filtered/deduped in-process, then wrote to DB.
- **After**: Publishes each fetched message to RabbitMQ immediately after fetch, skipping only already-seen links (optimization). DB reads are now purely to bound the fetch window and avoid re-publishing.
- **Benefit**: Decoupled from processing; if a source is slow, it doesn't block others. Hourly cron still drives scheduling.

### Worker (worker.py) - NEW
- Long-running process consuming from "jobs.raw" queue.
- Per-message decision logic:
  1. Deserialize Message from JSON
  2. Run KeywordFilter with rule-based logic (required/any/exclude, not OR-of-ANDs)
  3. If rejected: log and ack (no DB write, matches original "don't store rejected jobs")
  4. If passed:
     - Record which keywords matched (stamped in JSONB `matched_keywords`)
     - Generate fingerprint (SHA256 hash of normalized description text)
     - Check UNIQUE constraints (link + fingerprint)
     - Write to DB or skip if duplicate
  5. On exception: nack without requeue → goes to DLQ for manual inspection

### Filter Rules (config.py)
- **Before**: OR-of-ANDs: `KEYWORDS = [["PHP", "Senior"], ["backend", "senior"]]`
- **After**: Named rule groups in `FILTER_RULES`:
  ```json
  {
    "required": ["php"],           // All must match
    "any": ["developer", "engineer"],  // At least one must match
    "exclude": ["wordpress", "intern"]  // None may match
  }
  ```
- **Benefit**: Clearer intent, easier to tune, supports negative keywords.

### Deduplication (database/repository.py)
- **Link UNIQUE**: Original constraint, still enforced.
- **Fingerprint UNIQUE**: NEW. Catches the same job cross-posted verbatim across multiple channels (e.g., same Telegram bot reposts to two channels).
  - Fingerprint = SHA256(normalized_description)
  - Prevents duplicates that might have different URLs but identical content
- **Benefit**: Supports scenarios where sources republish without changing the text.

### Database Schema Extensions (database/connection.py)
- New columns (added via idempotent `ALTER TABLE IF NOT EXISTS`):
  - `fingerprint TEXT UNIQUE` — content hash for dedup
  - `matched_keywords JSONB` — which keywords matched this job (e.g., `["php", "symfony", "backend"]`)
- **Benefit**: Matched keywords visible in UI/API for transparency; fingerprint enables content-based dedup.

### JSON Serialization (models/message.py)
- New methods: `to_json()` and `from_json()` for RabbitMQ message serialization.
- Handles `datetime` encoding/decoding as ISO 8601 strings.

## Deployment (docker-compose.yml)

```yaml
services:
  postgres:
    # Unchanged, with added healthcheck for dependency ordering

  rabbitmq:
    image: rabbitmq:4-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: vacancier
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "127.0.0.1:15672:15672"  # Management UI (localhost only)
    healthcheck: rabbitmq-diagnostics -q ping

  vacancier-parser:
    build: ../vacancier-parser-v2
    command: # defaults to supercronic (crontab) — producer cron
    environment:
      DATABASE_URL: postgresql://...
      RABBITMQ_URL: amqp://vacancier:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    depends_on:
      postgres: { condition: service_healthy }
      rabbitmq: { condition: service_healthy }

  vacancier-worker:  # NEW
    build: ../vacancier-parser-v2
    command: ["python", "worker.py"]  # Override default ENTRYPOINT
    environment:
      DATABASE_URL: postgresql://...
      RABBITMQ_URL: amqp://vacancier:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    depends_on:
      postgres: { condition: service_healthy }
      rabbitmq: { condition: service_healthy }

  vacancier-tg-bot: # Unchanged
  vacancier-ui:     # Unchanged

volumes:
  postgres_data:
  rabbitmq_data:  # NEW
```

## Configuration (config.py)

Environment variables:

### Existing (unchanged)
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING` — Telegram credentials
- `HH_KEYWORDS`, `HH_AREA` — HeadHunter search parameters
- `REMOTEOK_TAGS` — RemoteOK tag filter (if empty, all jobs)
- `LINKEDIN_KEYWORDS` — LinkedIn search terms (if empty, LinkedIn fetcher disabled)
- `RSS_FEEDS` — List of RSS feed URLs
- `DATABASE_URL` — PostgreSQL connection string

### New
- `RABBITMQ_URL` — RabbitMQ AMQP URL (default: `amqp://guest:guest@localhost:5672/`)
- `FILTER_RULES` — JSON object with `required`, `any`, `exclude` keyword groups (default: PHP-focused rules)

Example:
```bash
export FILTER_RULES='{"required": ["python"], "any": ["engineer"], "exclude": ["django"]}'
export RABBITMQ_URL="amqp://vacancier:secure_password@rabbitmq:5672/"
```

## Running Locally

### 1. Start infrastructure
```bash
cd vacancier-infra
docker compose up -d
```

### 2. Check RabbitMQ is healthy
```bash
# Management UI at http://127.0.0.1:15672 (user: vacancier)
# Or via CLI:
docker compose exec rabbitmq rabbitmqctl list_queues
```

### 3. Trigger a producer run (one-time fetch)
```bash
# Either wait for cron to fire hourly, or manually trigger:
docker compose run --rm vacancier-parser python parser.py
```

### 4. Watch the worker consume
```bash
docker compose logs -f vacancier-worker
```

### 5. Check the database
```bash
docker compose exec postgres psql -U vacancier -d vacancier -c "SELECT * FROM messages LIMIT 5;"
```

## Testing

All existing tests pass with the new filter interface:

```bash
cd vacancier-parser-v2
python3 -m pytest tests/ -v
```

Tests cover:
- `KeywordFilter` with required/any/exclude rules
- `MessageProcessor` with the new FilterResult return type
- `DuplicateChecker` (unchanged)
- Integration scenarios with real filter + dedup collaborators

## Fallback

The original `vacancier-parser` directory is left untouched as a fallback. If issues arise with v2, you can revert `docker-compose.yml` to point at `../vacancier-parser` instead of `../vacancier-parser-v2` and redeploy.

## Future Enhancements

1. **Multi-worker scaling**: `vacancier-worker` service can be scaled to N replicas via `docker-compose scale` or Kubernetes replicas for higher throughput.

2. **AI ranking** downstream: Add a new consumer that reads from `jobs.raw` and pipes high-confidence matches to an AI scorer, bypassing the keyword filter entirely. Fingerprint-based dedup is independent, so no conflicts.

3. **Per-source metrics**: Publish fetch counts/success rates to Prometheus; currently structured log lines are sufficient.

4. **Dead letter queue inspection**: `jobs.raw.dlq` accumulates poison messages; add an occasional manual inspection tool or UI to diagnose/replay them.

5. **Filter rule tuning**: Make `FILTER_RULES` reloadable without restart (e.g., watch for a config file change, or expose an HTTP endpoint in the worker).

## Troubleshooting

### Queue is stuck/not consuming
1. Check worker is running: `docker compose logs vacancier-worker`
2. Check RabbitMQ is healthy: `docker compose exec rabbitmq rabbitmqctl status`
3. Check message format: `docker compose exec rabbitmq rabbitmqctl list_messages jobs.raw` (if available in your RabbitMQ version)

### Messages are going to DLQ
1. Check worker logs for errors: `docker compose logs vacancier-worker --tail 50`
2. Inspect DLQ: `docker compose exec rabbitmq rabbitmqctl list_queues jobs.raw.dlq`
3. Common causes: JSON decode error, filter rule misconfiguration

### High database inserts but low queue depth
1. Queue is working, worker is consuming successfully.
2. If you see many duplicates by fingerprint, your fetchers may be repuplicating content; consider tuning fetch windows or sources.

### Fingerprint UNIQUE violations in DB
This is not an error—the ON CONFLICT DO NOTHING clause silently skips duplicates. The worker logs `Duplicate by fingerprint` and acks the message, so it's removed from the queue.
