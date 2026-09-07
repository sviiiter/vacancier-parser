import psycopg2.extensions

from processor.matcher_protocol import MatchProcessor


class OpenAIMatcher(MatchProcessor):
    """Match messages against filters using OpenAI API (async evaluation)."""

    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def match_message(self, message_id: int, description: str, filters: list[dict]) -> list[int]:
        """
        Match a message against OpenAI-based filters.

        For now, returns empty list as placeholder.
        TODO: Implement OpenAI API call to match message against filter prompts.
        """
        # TODO: Call OpenAI API with the message description and filter content
        # Compare the response against the filter criteria
        return []
