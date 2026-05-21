from models.message import Message


class KeywordFilter:
    def __init__(self, keyword_groups: list[list[str]]) -> None:
        self._keyword_groups = [[kw.lower() for kw in group] for group in keyword_groups]

    def matches(self, message: Message) -> bool:
        text = message.description.lower()
        return any(all(kw in text for kw in group) for group in self._keyword_groups)
