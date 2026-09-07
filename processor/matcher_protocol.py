from abc import ABC, abstractmethod


class MatchProcessor(ABC):
    """Abstract interface for matching messages against filters."""

    @abstractmethod
    def match_message(self, message_id: int, description: str, filters: list[dict]) -> list[int]:
        """
        Match a single message against all filters.

        Args:
            message_id: ID of the message
            description: Message description/content to match against
            filters: List of filter dicts from the database

        Returns:
            List of filter IDs that matched the message
        """
        pass
