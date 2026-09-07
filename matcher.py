import logging
import os
import sys

import redis

from cache.publisher import CachePublisher
from config import REDIS_URL
from database.connection import get_connection, init_schema
from database.filter_repository import FilterRepository
from processor.keyword_matcher import KeywordMatcher
from processor.openai_matcher import OpenAIMatcher
from processor.matcher_protocol import MatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def _match_messages(
    conn,
    filter_repo: FilterRepository,
    keyword_matcher: MatchProcessor,
    openai_matcher: MatchProcessor,
    message_id: int = None,
) -> None:
    """Match messages against all filters using type-specific matcher processors.

    Args:
        conn: Database connection
        filter_repo: Filter repository
        keyword_matcher: Matcher for 'json' type filters
        openai_matcher: Matcher for 'file' type filters
        message_id: Optional specific message_id to match. If None, matches all untagged.
    """
    # Step 1: Get all filters and separate by type
    all_filters = filter_repo.list_filters()
    if not all_filters:
        log.info("No filters found")
        return

    json_filters = [f for f in all_filters if f.get("type") == "json"]
    file_filters = [f for f in all_filters if f.get("type") == "file"]

    log.info("Loaded %d JSON filters and %d OpenAI filters", len(json_filters), len(file_filters))

    # Step 2: Get messages to process
    with conn.cursor() as cur:
        if message_id:
            cur.execute(
                """
                SELECT m.id, m.description
                FROM messages m
                WHERE m.id = %s
                """,
                (message_id,),
            )
        else:
            cur.execute(
                """
                SELECT m.id, m.description
                FROM messages m
                WHERE NOT EXISTS (
                    SELECT 1 FROM message_filters mf WHERE mf.message_id = m.id
                )
                ORDER BY m.created_date ASC
                """
            )
        messages = cur.fetchall()

    # Step 3: For each message, match against filters of each type
    for msg_row in messages:
        msg_id = msg_row["id"]
        description = msg_row["description"]
        matched_filter_ids = []

        # Match against JSON (keyword) filters
        if json_filters:
            matched_filter_ids.extend(
                keyword_matcher.match_message(msg_id, description, json_filters)
            )

        # Match against file (OpenAI) filters
        if file_filters:
            matched_filter_ids.extend(
                openai_matcher.match_message(msg_id, description, file_filters)
            )

        # Step 4: Save message-filter relationships
        if matched_filter_ids:
            filter_repo.save_message_filters(msg_id, matched_filter_ids)
            log.debug("Tagged message id=%d with %d filter(s)", msg_id, len(matched_filter_ids))


def run() -> None:
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        log.error("DATABASE_URL not set")
        sys.exit(1)

    conn = get_connection(database_url)
    init_schema(conn)
    filter_repo = FilterRepository(conn)
    redis_client = redis.from_url(REDIS_URL)

    # Create type-specific matcher processors
    keyword_matcher: MatchProcessor = KeywordMatcher(conn)
    openai_matcher: MatchProcessor = OpenAIMatcher(conn)

    try:
        log.info("Starting matcher job")

        # Step 1: Match all untagged messages against all filters
        _match_messages(conn, filter_repo, keyword_matcher, openai_matcher)

        # Step 2: Publish matched messages to Redis for subscribers
        log.info("Publishing messages to Redis cache")
        cache_publisher = CachePublisher(conn, redis_client)
        cache_publisher.publish_for_subscribers()

        log.info("Matcher job completed")

    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)
    finally:
        conn.close()
        redis_client.close()


if __name__ == "__main__":
    run()
