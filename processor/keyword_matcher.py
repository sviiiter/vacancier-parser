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

        Filter rules structure in extra field:
        {
            "required": ["keyword1", "keyword2"],  # ALL must be present
            "any": ["keyword3", "keyword4"],       # AT LEAST ONE must be present
            "exclude": ["keyword5", "keyword6"]    # NONE should be present
        }

        Returns filter IDs that matched the message.
        """
        if not description:
            return []

        text = description.lower()
        matched_filter_ids = []

        for f in filters:
            if not f.get("extra"):
                continue

            try:
                rules = json.loads(f["extra"])
            except (json.JSONDecodeError, TypeError):
                continue

            if self._matches(text, rules):
                matched_filter_ids.append(f["id"])

        return matched_filter_ids

    @staticmethod
    def _matches(text: str, rules: dict) -> bool:
        """Check if text matches the filter rules."""
        # Check required keywords - ALL must be present
        required = rules.get("required", [])
        if required and not all(kw.lower() in text for kw in required):
            return False

        # Check any keywords - AT LEAST ONE must be present
        any_keywords = rules.get("any", [])
        if any_keywords and not any(kw.lower() in text for kw in any_keywords):
            return False

        # Check exclude keywords - NONE should be present
        exclude = rules.get("exclude", [])
        if exclude and any(kw.lower() in text for kw in exclude):
            return False

        # If we have at least one rule type and passed all checks, match
        if required or any_keywords or exclude:
            return True

        # No rules defined, no match
        return False
