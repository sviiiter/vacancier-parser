import json
import psycopg2.extensions

from processor.matcher_protocol import MatchProcessor


class KeywordMatcher(MatchProcessor):
    """Match messages against filters using keyword matching."""

    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def match_message(self, message_id: int, description: str, filters: list[dict]) -> list[int]:
        """
        Match a message against JSON (keyword) filters.

        Returns filter IDs that matched the message.
        """
        if not description:
            return []

        text = description.lower()
        matched_filter_ids = []

        for f in filters:
            keywords = []
            if f.get("extra"):
                try:
                    keywords = json.loads(f["extra"])
                except (json.JSONDecodeError, TypeError):
                    keywords = []

            if any(kw.lower() in text for kw in keywords):
                matched_filter_ids.append(f["id"])

        return matched_filter_ids
