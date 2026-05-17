from models.message import Message


class DuplicateChecker:
    def __init__(self, seen_links: set[str] | None = None) -> None:
        self._seen: set[str] = seen_links if seen_links is not None else set()

    def is_duplicate(self, message: Message) -> bool:
        if message.tg_message_link in self._seen:
            return True
        self._seen.add(message.tg_message_link)
        return False
